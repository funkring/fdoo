# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

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

from openerp.osv import fields,osv

class sale_order(osv.osv):

    _inherit = "sale.order"

    def onchange_shop_id(self, cr, uid, ids, shop_id, state, context=None):
        res = super(sale_order,self).onchange_shop_id(cr, uid, ids, shop_id, state, context=context)
        value = res.get("value",{})
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
            if shop.sale_category_id:
                value["sale_category_id"] = shop.sale_category_id.id
        return {'value': value}

    def onchange_partner_id2(self, cr, uid, ids, part_id,shop_id):
        res = super(sale_order,self).onchange_partner_id2(cr,uid,ids,part_id, shop_id)
        value = res.get("value")
        if value and part_id:
            partner_obj = self.pool.get("res.partner")
            partner = partner_obj.browse(cr, uid, part_id)
            category_id = partner.shop_id.sale_category_id
            if category_id:
                value["sale_category_id"] = category_id.id
        return res

    _columns = {
        "sale_category_id" : fields.many2one("sale.category", "Category")
    }

class sale_shop(osv.osv):

    _inherit = "sale.shop"

    _columns = {
        "sale_category_id" : fields.many2one("sale.category", "Category")
    }
