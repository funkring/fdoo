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

class crm_lead(osv.osv):
    _inherit = "crm.lead"
    
    def _browse_address(self,cr,uid,id):
        obj = self.browse(cr, uid, id)        
        return obj.partner_address_id or (obj.partner_id and obj.partner_id.partner_address_id) or obj
    
    def _get_address_phone(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for oid in ids:            
            address = self._browse_address(cr,uid,oid)
            if address:
                res[oid] = address.phone                       
        return res    
    
    def _get_address_mail(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for oid in ids:            
            address = self._browse_address(cr,uid,oid)
            if address:
                res[oid] = address.email                       
        return res    
    
    _columns = {
        "partner_address_phone" : fields.function(_get_address_phone,type="char",readonly=True,string="Phone"),
        "partner_address_email" : fields.function(_get_address_mail,type="char",readonly=True,string="E-Mail"),
        'create_uid':fields.many2one("res.users", "Created By", readonly=True)
    }    
    
    def onchange_partner_address_id2(self, cr, uid, ids,address_id):
        if address_id:
            address = self.pool.get("res.partner.address").browse(cr,uid,address_id)
            if address.partner_id:
                return {"value" : { "partner_id" : address.partner_id.id } }
        
        return {}
crm_lead()