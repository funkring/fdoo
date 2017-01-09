# -*- coding: utf-8 -*-
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
from openerp.addons.at_base import util
import openerp.addons.decimal_precision as dp


class sale_shop(osv.osv):
            
    _inherit = "sale.shop"
    _columns = {
        "product_category_ids" : fields.many2many("product.category", "shop_product_category_rel", "shop_id", "category_id", "Product Categories")
    }


class sale_order(osv.osv):
   
    def onchange_shop_id(self, cr, uid, ids, shop_id, state, project_id, context=None):
        res = super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id, state, project_id, context=context)
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
            categories  = shop.product_category_ids
            if not categories:
                res["value"]["shop_category_ids"] = self.pool["product.category"].search(cr, uid, [("parent_id","=",False)])
            else:
                res["value"]["shop_category_ids"] = [c.id for c in categories]
        return res
   
    def _shop_category_ids(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids)
        category_obj = self.pool["product.category"]
        for order in self.browse(cr, uid, ids, context):
            categories = order.shop_id.product_category_ids
            if not categories:
                res[order.id] = category_obj.search(cr, uid, [("parent_id","=",False)])
            else:
                res[order.id] = [c.id for c in categories]
        return res

   
    def _default_shop_id(self, cr, uid, context=None):
        # check default shop from user
        shop_ref = self.pool["res.users"].read(cr, uid, uid, ["shop_id"], context=context)["shop_id"]
        if shop_ref:
            return shop_ref[0]
        return super(sale_order, self)._default_shop_id(cr, uid, context=context)
    
    _inherit = "sale.order"
    _columns = {
        "shop_category_ids" : fields.function(_shop_category_ids, string="Product Categories", readonly=True, type="many2many", relation="product.category")
     }
    _defaults = {
        "shop_id" : _default_shop_id
    }