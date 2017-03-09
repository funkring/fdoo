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
from openerp.tools.translate import _

class account_invoice(osv.osv):

    def _calc_product_commission(self, cr, uid, ids, force=False, context=None):
        commission_obj = self.pool.get("commission_product.commission")
        invoice_obj = self.pool.get("account.invoice")
        commission_line_obj = self.pool.get("commission.line")
        for invoice in self.browse(cr, uid, ids, context=context):
            """ Create Analytic lines for invoice """
            company = invoice.company_id
            if company.commission_type == "invoice" or (force and invoice.type in ("out_refund","in_invoice")):
                
                sign = 1
                # change sign on in invoice or out refund
                if invoice.type in ("in_invoice", "out_refund"):
                    sign = -1
                    
                for line in invoice.invoice_line:
                    product = line.product_id
                    analytic_account = line.account_analytic_id
                    if analytic_account and product:
                        ref = invoice.number
                        orders = [l.order_id for l in line.sale_order_line_ids]
                        order_names = [o.name for o in orders]
                        order_date =  orders and min([o.date_order for o in orders]) or None
                        commission_date = order_date or invoice.date_invoice
                        price_subtotal = line.price_subtotal*sign
                            
                        commission_lines = commission_line_obj._get_product_commission(cr, uid, 
                                                         line.name, 
                                                         product,
                                                         line.quantity,
                                                         price_subtotal,
                                                         commission_date,
                                                         defaults={
                                                           "account_id" : analytic_account.id,
                                                           "invoice_line_id" : line.id,
                                                           "ref": ":".join(order_names) or ref or None,
                                                           "sale_partner_id" : invoice.partner_id.id,
                                                           "sale_product_id" : line.product_id.id   
                                                         },
                                                          context=context
                                                        )
                        
                        for commission_line in commission_lines:
                            commission_line_id = commission_line_obj.search_id(cr, uid, [("invoice_line_id", "=", line.id), 
                                                                                         ("partner_id", "=", commission_line["partner_id"]),
                                                                                         ("product_id", "=", commission_line["product_id"])], 
                                                                                         context=context)
                            
                            if commission_line_id:
                                commission_line_obj.write(cr, uid, commission_line_id, commission_line, context=context)
                            else:
                                commission_line_obj.create(cr, uid, commission_line, context=context)

    def action_move_create(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).action_move_create(cr, uid, ids, context=context)
        self._calc_product_commission(cr, uid, ids, context=context)
        return res

    _inherit = "account.invoice"
