#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martinr@funkring.net>
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

from openerp.osv import fields,osv
from openerp.tools.translate import _
import util
import re

class res_partner_title(osv.Model):   
    _inherit = "res.partner.title"
    _columns = {
        "mail_salutation": fields.text("Mail Salutation",translate=True),
        "co_salutation" : fields.text("C/O Salutation",translate=True)        
    }    

class res_partner(osv.osv):    
    
    def _check_for_ref(self,cr,uid,vals,context=None):
        if not vals.get("ref",False) and (vals.get("customer",False) or vals.get("supplier",False)):
            vals["ref"]=self.pool.get('ir.sequence').get(cr, uid, 'res.partner')
              
    def write(self, cr, uid, ids, vals, context=None):
        ids = util.idList(ids) 
        if len(ids) == 1:
            self._check_for_ref(cr,uid,vals,context)            
        return super(res_partner,self).write(cr,uid,ids,vals,context)            
    
    def create(self, cr, uid, vals, context=None):
        self._check_for_ref(cr,uid,vals,context)
        return super(res_partner,self).create(cr,uid,vals,context)
    
    def _get_mail_salutation(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)    
        for obj in self.browse(cr, uid, ids, context):                    
            salutation = obj.title and obj.title.mail_salutation or None
            name = obj.name
            if salutation:
                salutation = _(salutation)                
                if salutation:
                    if "%" in salutation:
                        res[obj.id] = salutation % name
                    else:
                        res[obj.id] = salutation
            else:
                res[obj.id]=name        
        return res       
    
    def _get_co_salutation(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)    
        for obj in self.browse(cr, uid, ids, context):                    
            salutation = obj.title and obj.title.co_salutation or None
            name = obj.name
            if salutation:
                salutation = _(salutation)                
                if salutation:
                    if "%" in salutation:
                        res[obj.id] = salutation % name
                    else:
                        res[obj.id] = salutation
            else:
                res[obj.id]=name        
        return res
      
    def _build_address_text(self, cr, uid, address, without_company=None, address_type=False, context=None):
        """
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the _country where it belongs.

        :param address: browse record of the res.partner to format
        :param without_company: address with company name
        :param address_type: the address type (supported types: None,mail)  
        :returns: the address formatted in a display that fit its _country habits (or the default ones
            if not _country is specified)
        :rtype: string
        """
                
        _lines = []
        
        #check default value
        if without_company is None and address_type == "mail":
            without_company = address.mail_without_company
                
        _use_parent_address = address.use_parent_address
        _mail_address = _use_parent_address and address.parent_id or address
        _name_address = not without_company and address.parent_id or address
                           
        #check if it is for mail     
        if address_type == "mail":
            #build name
            title = _name_address.title        
            _lines.append(title and " ".join((title.name,_name_address.name)) or _name_address.name)
            #build co
            if _name_address != address:
                co_salutation = address.co_salutation
                if co_salutation: 
                    _lines.append(co_salutation)
        #check with company
        elif _name_address != address:
            _lines.append(_name_address.name)
        elif _mail_address:
            _lines.append(_mail_address.name)
            
        _street = _mail_address.street
        _street2 = _mail_address.street2
        _zip = _mail_address.zip
        _city = _mail_address.city
        _state = _mail_address.state_id
        _country = _mail_address.country_id
        
        if _street: 
            _lines.append(_street)            
        
        if _street2:
            _lines.append(_street2)
        
        _values = []
        if _state and _state.code:
            _values.append(_state.code)
        if _zip:
            _values.append(_zip)
        if _city:
            _values.append(_city)
        if _values:
            _lines.append(" ".join(_values))   
            
        if _country and _country.name:
            _lines.append(_country.name)
                        
        return _lines
    
    def _display_address(self, cr, uid, address, without_company=None, context=None):
        return "\n".join(self._build_address_text(cr, uid, address, without_company=without_company, context=context))
    
    def _get_mail_address(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for partner in self.browse(cr, uid, ids, context):
            res[partner.id] = "\n".join(self._build_address_text(cr, uid, partner, address_type="mail", context=context))
        return res
    
    def _get_number(self, cr, uid, ids, num, context=None):
        return re.sub(r"[^0-9+]","", num)
    
    def _get_phone(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for partner in self.browse(cr, uid, ids, context):
            if partner.phone:
                res[partner.id] = self._get_number(cr, uid, ids, partner.phone)
        return res
    
    def _get_mobile(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for partner in self.browse(cr, uid, ids, context):
            if partner.mobile:
                res[partner.id] = self._get_number(cr, uid, ids, partner.mobile)
        return res
    
    def _get_fax(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for partner in self.browse(cr, uid, ids, context):
            if partner.fax:
                res[partner.id] = self._get_number(cr, uid, ids, partner.fax)
        return res
    
    _inherit = "res.partner"
    _columns =  {    
        "mail_without_company" : fields.boolean("Mail Address without company"),
        "mail_salutation" : fields.function(_get_mail_salutation, type="text",string="Mail Salutation"),
        "mail_address" : fields.function(_get_mail_address,type="text",string="Mail Address"),
        "co_salutation" : fields.function(_get_co_salutation, type="text", string="C/O Salutation"),
        "phone_n" : fields.function(_get_phone, type="char", store=True, string="Phone normalized"),
        "mobile_n" : fields.function(_get_mobile, type="char", store=True, string="Mobile normalized"),
        "fax_n" : fields.function(_get_fax, type="char", store=True, string="Fax normalized"),
        "birthday" : fields.date("Birthday")
     }
