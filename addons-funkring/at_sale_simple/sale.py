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

class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
        "opportunity_id" : fields.many2one("crm.lead","Opportunity",ondelete="set null", help="Optional linked opportunity")
    }   
     
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(sale_order,self).default_get(cr,uid,fields_list,context)
        if res.has_key("opportunity_id"):
            opportunity_id = res["opportunity_id"]
            if opportunity_id:
                opportunity = self.pool.get("crm.lead").browse(cr,uid,opportunity_id)
                
                if "partner_id" in fields_list:
                    res["partner_id"] = res.get("partner_id",opportunity.partner_id.id or False)
                                           
                if "shipping_address_id" in fields_list:
                    res["shipping_address_id"] = res.get("shipping_address_id",opportunity.partner_address_id.id or False)
                                  
            
        return res    
        
sale_order()
