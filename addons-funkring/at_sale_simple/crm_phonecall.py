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

from openerp.osv import osv

class crm_phonecall(osv.osv):    
    _inherit = "crm.phonecall"
        
    def onchange_partner_address_id(self, cr, uid, ids, add, email=False):
        res = super(crm_phonecall, self).onchange_partner_address_id(cr, uid, ids, add, email)
        if add and not res.has_key("partner_id") or not res["partner_id"]:
            address = self.pool.get('res.partner.address').browse(cr, uid, add)
            res["partner_id"]=address.partner_id.id
        return res
    
    def onchange_opportunity_id(self,cr,uid,ids,add):
        res = {}
        if add:
            opportunity = self.pool.get("crm.lead").browse(cr,uid,add)
            if opportunity.partner_address_id or opportunity.partner_id:
                res["partner_id"] = opportunity.partner_address_id.partner_id.id or opportunity.partner_id.id
                
            if opportunity.partner_address_id:
                res["partner_address_id"] = opportunity.partner_address_id.id             
        return res    
crm_phonecall()