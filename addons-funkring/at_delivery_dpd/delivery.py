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

from pyPdf import PdfFileWriter, PdfFileReader
from HTMLParser import HTMLParser

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import logging
_logger = logging.getLogger(__name__) 


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
            logger = logging.getLogger('zeep.transports')
            logger.setLevel(logging.DEBUG)
            logger.propagate = True
            
        return self._dpd_client
    
    def _dpd_error(self, e):
        _logger.exception(e)
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
        
        
        # check packages        
        pack_op_obj = self.pool["stock.pack.operation"]        
        package_count = 0
        package_count_all = True
        
        # check operation for package count
        for operation in picking.pack_operation_ids:
            if operation.qty_done:
                # check if all operation have a package count
                # if not add one package for itself
                if not operation.package_count:
                    if package_count_all:
                        package_count_all = False
                        package_count += 1
                else:
                    # add packages
                    package_count += operation.package_count
        
        if not package_count:
            package_count = 1
        
        partner = picking.partner_id
        client = self._dpd_client_get(context)      
        
        tracking_refs = []
        carrier_errors = []
        label_pdf = PdfFileWriter()
        carrier_label_name = None        
        try:
            
            for packageNo in range(0, package_count):
          
                parts = {}
                parts["username"] = profile.user            
                parts["password"] = md5(profile.password).hexdigest()
                parts["mandant"] = profile.client
                parts["kdnr"] = partner.ref or ""
                              
                name = partner.name or ""
                zusatz = ""
                
                if len(name) > 48:
                    shortName = name[:48]
                    lastSpacePos = shortName.rfind(" ")
                    if lastSpacePos > 30:
                        lastSpacePos+=1
                        zusatz = name[lastSpacePos:lastSpacePos+32]
                        name = shortName[:lastSpacePos]                        
                    else:
                        zusatz = name[48:80]
                        name = shortName

                parts["name"] = name
                parts["zusatz"] = zusatz
                
                parts["anschrift"] = partner.street and partner.street.strip() or ""         
                parts["plz"] = partner.zip and partner.zip.strip() or  ""
                parts["ort"] = partner.city and partner.city.strip() or ""
                parts["land"] = partner.country_id and partner.country_id.code or "AT"
                 
                parts["bezugsp"] = partner.street2 and partner.street2.strip() or ""
                parts["tel"] = partner.phone or partner.mobile or ""
                parts["mail"] = partner.email or ""
                parts["liefernr"] = picking.name or ""
                parts["pakettyp"] = carrier.dpd_type or "DPD"
                
                parts["gewicht"] = "1000"
                weight = picking.carrier_weight or picking.weight or 0.0
                if weight:
                    uom_obj = self.pool["product.uom"]
                    uom_id = uom_obj.search_id(cr, uid, [("category_id","=",picking.weight_uom_id.category_id.id),'|',("name","=","g"),("code","=","g")])
                    uom = uom_obj.browse(cr, uid, uom_id, context=context)
                    if not uom:
                        raise Warning(_("No unit gramm found!"))            
                    parts["gewicht"] = str(int(uom_obj._compute_qty(cr, uid, picking.weight_uom_id.id, weight, uom.id))) 
                          
                parts["vdat"] = ""            
                
                produkt1 = carrier.dpd_product1
                if not produkt1:
                    produkt1 = "KP"
                    if weight > 3:
                        produkt1 = "NP"
                
                parts["produkt1"] = produkt1
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
                    carrier_label_name = label_url.split("/")[-1]
                    label_file = urllib2.urlopen(label_url)
                    try:                    
                        # add page
                        label_pdf.addPage(PdfFileReader(StringIO(label_file.read())).getPage(0))
                    finally:
                        label_file.close()
                
                # evaluate error
                err_code = msgSoapOut.err_code            
                if err_code:               
                    carrier_error = err_code
                    foundError = False
                    for err, err_message in self._dpd_errors:
                        if err in err_code:
                            carrier_error = err_message
                            foundError = True
                            
                    if not foundError:
                        h = HTMLParser()
                        carrier_error = h.unescape(carrier_error)
                        
                    _logger.error(carrier_error)
                    carrier_errors.append(carrier_error)
                else:
                    # store ref
                    tracking_refs.append(msgSoapOut.paknr)
                    
            
            # build label           
            carrier_label = None
            if label_pdf.getNumPages() > 0:
                bufPdf = StringIO()
                try:
                    label_pdf.write(bufPdf)
                    carrier_label = base64.encodestring(bufPdf.getvalue())
                finally:
                    bufPdf.close()                
                
            status = None
            if not carrier_errors:
                status = "created"
                
            # write data
            picking_obj.write(cr, uid, picking.id, {
                "carrier_label_name": carrier_label_name,
                "carrier_label": carrier_label,
                "carrier_error": "\n".join(carrier_errors),
                "carrier_tracking_ref": ", ".join(tracking_refs),
                "carrier_status" : status,
                "number_of_packages" : package_count
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
        
        profile = carrier.dpd_profile_id
        if not profile:
            raise Warning(_("No DPD Profile defined!"))
        
        picking_obj = self.pool["stock.picking"]
        client = self._dpd_client_get(context)
        try:
            if picking.carrier_tracking_ref:
                for tracking_ref in picking.carrier_tracking_ref.split(", "):        
                    parts = {}
                    parts["username"] = profile.user            
                    parts["password"] = md5(profile.password).hexdigest()
                    parts["mandant"] = profile.client
                    parts["paknr"] = tracking_ref
                    
                    msgSoapOut = client.service.cancelByTracknr(**parts)
                               
                    # check status
                    if msgSoapOut.storno != "1" and msgSoapOut.err_code != "FR06":
                        raise Warning(_("Unable to cancel %s. Call DPD for manual cancel!") % tracking_ref)

            # update status
            picking_obj.write(cr, uid, picking.id, {                       
                "carrier_status" : None,
                "carrier_error" : None
            }, context=context)
                
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