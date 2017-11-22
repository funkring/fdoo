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

class sale_shop(osv.Model):
    _inherit = "sale.shop"
    _columns = {
        "country_ids" : fields.many2many("res.country", "sale_shop_country_rel", "shop_id", "country_id", "Countries")
    }
    

class sale_order(osv.Model):
    _inherit = "sale.order"
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None, shop_id=None):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, partner_id, context=context, shop_id=shop_id)
        
        # check if partner is set
        if partner_id:
            
            # browse partner
            partner = self.pool["res.partner"].browse(cr, uid, partner_id, context=context)
            if partner:
                country_id = partner.country_id.id
                # update country
                value = res["value"]
                value["country_id"] = country_id
                    
                # determine shop for country
                shop_obj = self.pool["sale.shop"]
                if not shop_id or not shop_obj.search(cr, uid, [("id","=",shop_id),'|',("country_ids","=",False),("country_ids","=",country_id)], count=True):
                  value["shop_id"] = shop_obj.search_id(cr, uid, ['|',("country_ids","=",False),("country_ids","=",country_id)]) or value.get("shop_id", shop_id)
                
        return res
    
    def _country_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = order.partner_id.country_id.id
        return res
    
    _columns = {
        "country_id" : fields.function(_country_id, string="Country", type="many2one", obj="res.country", store=False)
    }