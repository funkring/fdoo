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

from openerp.exceptions import Warning
from openerp.tools.translate import _


class sale_shop(osv.osv):

    _inherit = "sale.shop"
    _columns = {
        "sender_address_id" : fields.many2one("res.partner", "Sender Address")
    }


class sale_order(osv.osv):
    
    _inherit = "sale.order"
    _columns = {
        "neutral_delivery" : fields.boolean("Neutral Delivery", states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    }
    

class sale_order_line(osv.osv):

    def _product_id_change(self, cr, uid, res, flag, product_id, partner_id, lang, context=None):
        if not flag:
            if product_id:
                context = {'lang': lang, 'partner_id': partner_id}
                product_obj = self.pool.get('product.product')

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
                                  lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, warehouse_id=False, route_id=False, context=None):

        res = super(sale_order_line, self).product_id_change_with_wh(cr, uid, ids, pricelist, product, qty=qty,
                                                                         uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
                                                                         lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging,
                                                                         fiscal_position=fiscal_position, flag=flag, warehouse_id=warehouse_id, route_id=route_id, context=context)

        if not context or not context.get("keep_warning"):
            warning = res.get("warning")
            if warning:
                res["value"]["available"] = False
                del res["warning"]
            else:
                res["value"]["available"] = True
            
        res =  self._product_id_change(cr, uid, res, flag, product, partner_id, lang, context=context)
        return res
    
    def action_available(self, cr, uid, ids, context=None):
        
        context = context and dict(context) or {}
        context["keep_warning"] = True
        
        for line in self.browse(cr, uid, ids, context=context):
            order = line.order_id
            
            res = self.product_id_change_with_wh(cr, uid, [line.id], order.pricelist_id.id, line.product_id.id, 
                                                 qty=line.product_uom_qty, uom=line.product_uom.id, 
                                                 qty_uos=line.product_uos_qty, uos=line.product_uos.id, 
                                                 name=line.name, 
                                                 partner_id=order.partner_id.id,
                                                 lang=False, update_tax=False, 
                                                 date_order=order.date_order, 
                                                 packaging=line.product_packaging.id,
                                                 fiscal_position=order.fiscal_position.id, 
                                                 flag=True,
                                                 warehouse_id=order.warehouse_id.id, 
                                                 route_id=line.route_id.id, 
                                                 context=context)
            
            warning = res.get("warning")
            if warning:
                raise Warning(warning["title"], warning["message"])
            
            # set to available
            self.write(cr, uid, line.id, {"available": True}, context=context)
            
        return True

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
        "supplier_id" : fields.many2one("res.partner", "Supplier"),
        "available_supplier_ids" : fields.function(_available_supplier_ids, string="Available Suppliers", type="many2many", relation="res.partner", store=False, readonly=True ),
        "procurement_note" : fields.text("Procurement Note"),
        "available" : fields.boolean("Available", copy=False)
    }  
