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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class commission_line(osv.osv):
                
    def unlink(self, cr, uid, ids, context=None):
        line_ids = []
        for obj in self.browse(cr, uid, ids, context=context):
            line_ids.append(obj.line_id.id)            
        self.pool.get("account.analytic.line").unlink(cr, uid, line_ids, context=context)
        return super(commission_line, self).unlink(cr, uid, ids, context=context)
        
    def _prov_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0.0)
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = obj.amount * -1.0
        return res
    
    def _short_name(self, name):
        if name:
            return name.split("\n")[0]
        return ""
        
    def onchange_commission(self, cr, uid, ids, total_commission, amount, price_sub, context=None):
        value = {}
        res = { "value" : value }
        sign = 1.0
        
        if amount < 0.0:
            sign = -1.0
        
        if total_commission:
            value["amount"] = price_sub * (total_commission / 100.0) * sign
              
        return res
    
    _columns = {
        "line_id": fields.many2one("account.analytic.line", "Analytic line", ondelete="cascade", required=True),        
        "base_commission" : fields.float("Base Commission %", required=True),
        "total_commission" : fields.float("Commission %", required=True),
        "invoice_line_id" : fields.many2one("account.invoice.line","Invoice Line", select=True),
        "invoice_id" : fields.related("invoice_line_id", "invoice_id", type="many2one", obj="account.invoice", string="Invoice", readonly=True, select=True, store=True),
        "order_line_id" : fields.many2one("sale.order.line", "Order Line" , select=True),
        "order_id" : fields.related("order_line_id", "order_id", type="many2one", obj="sale.order", string="Order", readonly=True, select=True, store=True),
        "period_id" : fields.many2one("account.period", string="Period", readonly=True, select=True, store=True, required=True),
        "sale_partner_id" : fields.many2one("res.partner", string="Customer", readonly=True, select=True, store=True),
        "sale_product_id" : fields.many2one("product.product", string="Product", readonly=True, select=True, store=True),
        "partner_id" : fields.many2one("res.partner","Provision Receiver", select=True),
        "invoiced_id" : fields.many2one("account.invoice","Invoiced", select=True, ondelete="set null"),
        "invoiced_line_ids" : fields.many2many("account.invoice.line", "commission_invoice_line_rel", "commission_line_id", "invoice_line_id", "Invoice Lines"),       
        "price_sub" : fields.float("Subtotal", digits_compute=dp.get_precision("Account")),
        "prov_amount" : fields.function(_prov_amount, string="Commission", type="float", store=False, digits_compute=dp.get_precision("Account"))
    }
    _name = "commission.line"
    _inherits = {"account.analytic.line": "line_id"}
    _order = "date"
