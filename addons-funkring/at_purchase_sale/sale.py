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

from openerp.osv import fields,osv
from openerp.addons.at_base import util
from openerp.addons.at_base.util import PRIORITY

class sale_shop(osv.osv):

    _inherit = "sale.shop"
    _columns = {
        "supplier_ships_default" : fields.boolean("Supplier Ships"),
        "neutral_delivery" : fields.boolean("Neutral Delivery"),
        "sender_address_id" : fields.many2one("res.partner", "Sender Address")
    }


class sale_order(osv.osv):

    def action_button_confirm(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)

        for order_id in ids:
            purchase_order_obj = self.pool["purchase.order"]
            purchase_order_ids = purchase_order_obj.search(cr, uid, [("sale_order_id", "=", order_id)])
            for purchase_order in purchase_order_obj.browse(cr, uid, purchase_order_ids):
                if purchase_order.state in ("draft", "sent"):
                    purchase_order_obj.action_cancel(cr, uid, [purchase_order.id], context=context)

        return res

    def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
        res = super(sale_order,self)._prepare_order_line_procurement(cr, uid, order, line, group_id, context=context )
        supplier_ships=line.supplier_ships or line.order_id.supplier_ships
        res["supplier_ships"]=supplier_ships
        if not res.get("account_analytic_id") and order.project_id:
            res["account_analytic_id"]=order.project_id.id
        if supplier_ships:
            res["dest_address_id"]=order.partner_shipping_id.id
        res["sale_order_id"]=order.id
        res["note"]=line.procurement_note
        return res

    def onchange_shop_id(self, cr, uid, ids, shop_id, state, context=None):
        res = super(sale_order,self).onchange_shop_id(cr, uid, ids, shop_id, state, context=context)
        value = res.get("value",None) or {}
        if shop_id:
            shop_rec = self.pool.get("sale.shop").browse(cr, uid, shop_id, context=context)
            value["supplier_ships"]=shop_rec.supplier_ships_default
        return {'value': value}

    _inherit = "sale.order"
    _columns = {
        "supplier_ships" : fields.boolean("Supplier Ships",readonly=True,states={"draft": [("readonly", False)]})
    }


class sale_order_line(osv.osv):

    def _product_id_change(self, cr, uid, res, flag, product_id, partner_id, lang, context=None):
        if not flag:
            if product_id:
                context = {'lang': lang, 'partner_id': partner_id}
                product_obj = self.pool.get('product.product')
                res["value"]["supplier_ships"]=product_obj.read(cr, uid, product_id, ["supplier_ships"], context=context)["supplier_ships"]

                product_context = context and context.copy() or {}
                product_context.update({'lang': lang, 'partner_id': partner_id})
                product_val = product_obj.browse(cr, uid, product_id, context=product_context)

                # set default seller
                if product_val and product_val.seller_ids:
                    seller_line_id = product_val.seller_ids[0]
                    util.setSubDictValue(res,"value","supplier_id",seller_line_id and seller_line_id.id or None)

                supplier_ids = self._supplier_ids(product_val)
                res["value"]["supplier_id"]=supplier_ids and supplier_ids[0] or None
                res["value"]["available_supplier_ids"]=[(6,0,supplier_ids)]
            else:
                res["supplier_id"]=None
                res["value"]["available_supplier_ids"]=[(6,0,[])]

        return res

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):

        res = super(sale_order_line,self).product_id_change(cr,uid,ids,pricelist,product,
                                                      qty=qty,uom=uom, qty_uos=qty_uos, uos=uos,
                                                      name=name, partner_id=partner_id,lang=lang,update_tax=update_tax,
                                                      date_order=date_order, packaging=packaging, fiscal_position=fiscal_position,flag=flag,context=context)

        return self._product_id_change(cr, uid, res, flag, product, partner_id, lang, context=context)

    def product_id_change_with_wh(self, cr, uid, ids, pricelist, product, qty=0,
                                  uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                                  lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, warehouse_id=False, context=None):

        res = super(sale_order_line, self).product_id_change_with_wh(cr, uid, ids, pricelist, product, qty=qty,
                                                                         uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
                                                                         lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging,
                                                                         fiscal_position=fiscal_position, flag=flag, warehouse_id=warehouse_id, context=context)

        return self._product_id_change(cr, uid, res, flag, product, partner_id, lang, context=context)

    def _supplier_ids(self, product):
        res = []
        if not product:
            return res
        for supplier in product.seller_ids:
            res.append(supplier.name.id)
        return res

    def _available_supplier_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for line in self.browse(cr, uid, ids, context):
            res[line.id]=self._supplier_ids(line.product_id)
        return res

    _inherit = "sale.order.line"
    _columns = {
        "supplier_ships" : fields.boolean("Supplier Ships",readonly=True,states={"draft": [("readonly", False)]}),
        "supplier_id" : fields.many2one("res.partner", "Selected Supplier"),
        "available_supplier_ids" : fields.function(_available_supplier_ids, string="Available Suppliers", type="many2many", relation="res.partner", store=False, readonly=True ),
        "priority": fields.selection(PRIORITY, "Priority"),
        "procurement_note" : fields.text("Procurement Note")
    }
    _defaults = {
        "priority" : PRIORITY[1][0]
    }
