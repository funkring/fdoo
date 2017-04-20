# -*- coding: utf-8 -*-
#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martin.reisenhofer@funkring.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.exceptions import Warning

from hashlib import md5
import urllib2
import base64

from zeep import Client
from zeep.xsd import SkipValue
from openerp.tools.translate import _


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import logging
logger = logging.getLogger(__name__) 


class delivery_carrier_dpd(osv.Model):
    _name = "delivery.carrier.dpd"
    _description = "DPD Profile"
    _columns = {
        "name" : fields.char("Name", required=True),
        "user" : fields.char("User", required=True),
        "password" : fields.char("Password", password=True, required=True),
        "client" : fields.integer("Client", required=True)
    }
    

class delivery_carrier(osv.Model):
    _inherit = "delivery.carrier"
    _dpd_client = None
    _dpd_errors = [ ("ER01","Username ist falsch."),
                    ("ER02","Passwort ist falsch."),
                    ("ER03","Mandantennummer ist falsch."),
                    ("ER04","Name fehlt oder beinhaltet zu viele Zeichen."),
                    ("ER05","Anschrift fehlt oder beinhaltet zu viele Zeichen."),
                    ("ER06","PLZ ist falsch, fehlt, oder beinhaltet ein Sonderzeichen."),
                    ("ER07","Ort fehlt oder beinhaltet zu viele Zeichen."),
                    ("ER08","Land fehlt oder falsches Länderkürzel"),
                    ("ER09","Telefonnummer fehlt (Pflichtig für primetime Versand)"),
                    ("ER10","Laufnummer fehlt"),
                    ("ER11","Versanddatum fehlerhaft"),
                    ("ER12","Gewichtsgrenze überschritten (31,5 kg)"),
                    ("ER13","Kundennummer und/oder Bezugsperson fehlt (Pflichtig für PaketShop Zustellung)"),
                    ("PR01","Falscher Wert im Produkt 1"),
                    ("PR01-fix","Falscher oder fehlender Wert für Service Fixtermin"),
                    ("PR01-X","Produkt nicht freigeschalten."),
                    ("PR02","Falscher Wert im Produkt 2"),
                    ("PR02-hv","Falscher oder fehlender Wert für Zusatzleistung Höherversicherung"),
                    ("PR02-asg","Falscher oder fehlender Wert für Zusatzleistung Abstellgenehmigung"),
                    ("PR02-id","Falscher oder fehlender Wert für Zusatzleistung Identitätsprüfung"),
                    ("PR02-abt","Falscher oder fehlender Wert für Zusatzleistung Abteilungsbelieferung"),
                    ("PR02-aviso","Falscher oder fehlender Wert für Zusatzleistung Aviso"), 
                    ("PR02-X","Falscher Wert im Produkt 3"),
                    ("PR03","Falscher oder fehlender Wert für Zusatzleistung DPD Nachnahme"), 
                    ("PR03-nachnahme","Falscher oder fehlender Wert für Zusatzleistung DPD Nachnahme"),
                    ("PR03-nnbar","Falscher oder fehlender Wert für Zusatzleistung primetime Nachnahme"),
                    ("PR03-X","Produkt nicht freigeschalten."),
                    ("PR04","Falscher Wert im Produkt 4"),
                    ("PR04-wp","Produkt nicht freigeschalten."),
                    ("PR05","Falscher Wert im Produkt 5"),
                    ("PR05-X","Produkt nicht freigeschalten."),
                    ("PR06","Falscher Wert im Produkt 6"),
                    ("PR06-aviso","Falscher oder fehlender Wert für Zusatzleistung Aviso"),
                    ("PR06-X","Produkt nicht freigeschalten."),
                    ("FR01","Username ist falsch."),
                    ("FR02","Passwort ist falsch."),
                    ("FR03","Mandantennummer ist falsch."),
                    ("FR04","Übergebene Paketscheinnummer für Paketscheinstorno ist nicht korrekt oder nicht vorhanden."),
                    ("FR05","Datumsangabe -format ist nicht korrekt."),
                    ("FR06","Paket bereits storniert.")                  
                  ]
                     
    def _api_select(self, cr, uid, context=None):
        res = super(delivery_carrier, self)._api_select(cr, uid, context=context)
        res.append(("dpd","DPD"))
        return res
    
    def _dpd_client_get(self, context=None):
        if self._dpd_client is None:
            self._dpd_client = Client("http://web.paketomat.at/webservice/service-1.0.2.php?wsdl")
#             logger = logging.getLogger('zeep.transports')
#             logger.setLevel(logging.DEBUG)
#             logger.propagate = True
            
        return self._dpd_client
    
    def _dpd_error(self, e):
        logger.exception(e)
        if hasattr(e, "message"):
            raise Warning(e.message)
        raise e
    
    def _dpd_label_get(self, cr, uid, picking, context=None):
        carrier = picking.carrier_id
        if not carrier or carrier.api != "dpd":
            raise Warning(_("Invalid carrier type!"))
        
        profile = carrier.dpd_profile_id
        if not profile:
            raise Warning(_("No DPD Profile defined!"))
        
        partner = picking.partner_id
        client = self._dpd_client_get(context)
        try:
            parts = {}
            
            parts["username"] = profile.user            
            parts["password"] = md5(profile.password).hexdigest()
            parts["mandant"] = profile.client
            parts["kdnr"] = partner.ref or ""
                          
            parts["name"] = partner.name or ""       
            parts["anschrift"] = partner.street or ""
            parts["zusatz"] = partner.street2 or ""
            parts["plz"] = partner.zip or ""
            parts["ort"] = partner.city or ""
            parts["land"] = partner.country_id and partner.country_id.code or "AT"
             
            parts["bezugsp"] = partner.name or ""
            parts["tel"] = partner.phone or partner.mobile or ""
            parts["mail"] = partner.email or ""
            parts["liefernr"] = picking.name or ""
            parts["pakettyp"] = carrier.dpd_type or "DPD"
              
            parts["gewicht"] = "1000" 
            if picking.weight:
                uom_obj = self.pool["product.uom"]
                uom_id = uom_obj.search_id(cr, uid, [("category_id","=",picking.weight_uom_id.category_id.id),'|',("name","=","g"),("code","=","g")])
                uom = uom_obj.browse(cr, uid, uom_id, context=context)
                if not uom:
                    raise Warning(_("No unit gramm found!"))            
                parts["gewicht"] = str(int(uom_obj._compute_qty(cr, uid, picking.weight_uom_id, picking.weight, uom))) 
                      
            parts["vdat"] = ""            
            parts["produkt1"] = carrier.dpd_product1 or "NP"
            parts["produkt2"] = []
            parts["produkt3"] = []
            parts["produkt4"] = []
            parts["produkt5"] = ""
            parts["produkt6"] = []
            parts["produkt7"] = ""
            
            msgSoapOut = client.service.getLabel(**parts)
            picking_obj = self.pool["stock.picking"]
             
            # save pdf
            label_url = msgSoapOut.label
            if label_url:
                label_file = urllib2.urlopen(label_url)
                buf = StringIO()
                base64.encode(label_file,buf)
                
                filename = label_url.split("/")[-1]
                picking_obj.write(cr, uid, picking.id, {
                    "carrier_label_name" : filename,
                    "carrier_label" : buf.getvalue()
                }, context=context)
                
            
            # evaluate error
            err_code = msgSoapOut.err_code            
            if err_code:
                message = []
                for err, err_message in self._dpd_errors:
                    if err in err_code:
                        message.append(err_message)
                        
                    
                if not message:
                    message.append(_("Error: %s") % err_code)
                
                # write error
                message = "\n".join(message)
                picking_obj.write(cr, uid, picking.id, {                       
                    "carrier_error" : message
                }, context=context)
                
            else:
                # update status
                tracking_no = msgSoapOut.paknr
                picking_obj.write(cr, uid, picking.id, {                       
                    "carrier_tracking_ref" : tracking_no,
                    "carrier_status" : "created",
                    "carrier_error" : None
                }, context=context)

        except Exception, e:            
            self._dpd_error(e)
            raise e
        
        return True
        
    def _dpd_cancel(self, cr, uid, picking, context=None):
        carrier = picking.carrier_id
        if not carrier or carrier.api != "dpd":
            raise Warning(_("Invalid carrier type!"))
        
        if picking.carrier_status != "created":
            raise Warning(_("Delivery could only canceled in state 'created'"))
        
        if not picking.carrier_tracking_ref:
            raise Warning(_("No tracking number!"))
        
        profile = carrier.dpd_profile_id
        if not profile:
            raise Warning(_("No DPD Profile defined!"))
        
        picking_obj = self.pool["stock.picking"]
        client = self._dpd_client_get(context)
        try:
            parts = {}
            parts["username"] = profile.user            
            parts["password"] = md5(profile.password).hexdigest()
            parts["mandant"] = profile.client
            parts["paknr"] = picking.carrier_tracking_ref
            
            msgSoapOut = client.service.cancelByTracknr(**parts)
                       
            # update status
            if msgSoapOut.storno == "1" or msgSoapOut.err_code == "FR06":
                tracking_no = msgSoapOut.paknr                
                picking_obj.write(cr, uid, picking.id, {                       
                    "carrier_tracking_ref" : tracking_no,
                    "carrier_status" : None,
                    "carrier_error" : None
                }, context=context)
            else:
                raise Warning(_("Cancel not possible, call your carrier"))
            
        except Exception, e:            
            self._dpd_error(e)
            raise e
        
        return True
   
    _columns = {
        "api" : fields.selection(_api_select, string="API"),
        "dpd_profile_id" : fields.many2one("delivery.carrier.dpd","DPD Profile"),
        "dpd_type" : fields.selection([("DPD","DPD"),
                                       ("PT","Prime Time"),
                                       ("B2C","B2C"),
                                       ("2S","2Shop Delivery")],
                                      string="Parcel Type"),
        "dpd_product1" : fields.selection([("NP","DPD/B2C Normal"),
                                           ("KP","DPD/B2C Small"),
                                           ("RETURN","DPD Return"),
                                           ("AM1","Service Business Day 09 AM"),
                                           ("AM2","Service Business Day 12 AM"),
                                           ("AM1-6","Service Saturday 09 AM"),
                                           ("AM2-6","Service Saturday 12 AM")],
                                          string="Product 1")
    }