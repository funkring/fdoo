# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

#############################################################################\
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

class account_invoice(osv.osv):
    
    def onchange_shop(self, cr, uid, ids, shop_id, company_id, part_id, type, invoice_line, currency_id):
        if shop_id and company_id:
            shop_obj = self.pool["sale.shop"]
            shop = shop_obj.browse(cr, uid, shop_id)
            if shop and shop.company_id and shop.company_id.id != company_id:
                new_company_id = shop.company_id.id
                res = self.onchange_company_id(cr, uid, ids, new_company_id, part_id, type, invoice_line, currency_id)
                res["value"]["company_id"] = new_company_id
                return res            
        return {}
    
    def _default_shop_id(self, cr, uid, context=None):
        company_id = self.pool["res.company"]._company_default_get(cr, uid, "account.invoice", context=context)
        res = None
        if company_id:
            shop_obj = self.pool["sale.shop"]
            res = shop_obj.search_id(cr, uid, [("company_id","=",company_id)],context=context)
            if not res:
                res = shop_obj.search_id(cr, uid, [("company_id","=",False)],context=context)
        return res
        
    def _get_performance_start(self, cr, uid, inv, context=None):
        order_date = None
        for order in inv.sale_order_ids:
            order_date = (not order_date and order.date_order) or min(order_date,order.date_order)
        return order_date or super(account_invoice, self)._get_performance_start(cr, uid, inv, context=context)
        
    _inherit = "account.invoice"
    _columns = {
        "sale_order_ids" : fields.many2many("sale.order","sale_order_invoice_rel","invoice_id","order_id","Orders",readonly=True),
        "shop_id" : fields.many2one("sale.shop", "Shop", required=True, readonly=True, states={"draft": [("readonly", False)]}, select=True)
    }
    _defaults = {
        "shop_id" : _default_shop_id
    }


class account_invoice_line(osv.osv):

    def _order_info(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids)
        for invoice_line in self.browse(cr, uid, ids):        
            order_lines = invoice_line.sale_order_line_ids
            if order_lines:
                for order_line in order_lines:
                    order = order_line.order_id
                    infos = []
                    if invoice_line.origin:
                        infos.append(invoice_line.origin)
                    if order.name and order.name != invoice_line.origin:
                        infos.append(order.name)
                    if order.client_order_ref:
                        infos.append(order.client_order_ref)
                    res[invoice_line.id] = " / ".join(infos)
            else:
                res[invoice_line.id] = invoice_line.origin
        return res

    _inherit = "account.invoice.line"
    _columns = {
        "order_info" : fields.function(_order_info, type="text", string="Order Info"),
        "sale_order_line_ids" : fields.many2many("sale.order.line", "sale_order_line_invoice_rel", "invoice_id", "order_line_id", "Sale Order Lines")
    }
