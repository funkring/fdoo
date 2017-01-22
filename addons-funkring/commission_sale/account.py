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
    
    def _calc_sale_commission(self, cr, uid, ids, context=None):   
        """ Create Analytic lines for invoice """        
        period_ids = set()
        salesman_ids = set()
        
        user_obj = self.pool.get("res.users")
        commission_line_obj = self.pool.get("commission.line")
        invoice_obj = self.pool.get("account.invoice")
        order_obj = self.pool.get("sale.order")
             
        for invoice in self.browse(cr, uid, ids, context=context):                       
            
            company = invoice.company_id
            if company.commission_type == "invoice" or invoice.type in ("out_refund","in_invoice"):

                sign = -1
                if invoice.type in ("out_invoice", "in_refund"):
                    sign = 1

                for line in invoice.invoice_line:
                    product = line.product_id
                    analytic_account = line.account_analytic_id
                    if analytic_account and product:     
                        
                        def create_commission(salesman_user, name=None, commission_date=None, ref=None, pricelist=None):
                            price_subtotal = sign*line.price_subtotal                            
                            commission_lines = commission_line_obj._get_sale_commission(cr, uid, 
                                                                 line.name, salesman_user, 
                                                                 invoice.partner_id, 
                                                                 product, 
                                                                 line.quantity, 
                                                                 price_subtotal, 
                                                                 date=commission_date or invoice.date_invoice, 
                                                                 pricelist=pricelist, 
                                                                 defaults={
                                                                    "ref": ref or invoice.number,
                                                                    "invoice_line_id" : line.id,
                                                                    "invoice_id" : invoice.id,
                                                                    "account_id": analytic_account.id,
                                                                    "sale_partner_id" : invoice.partner_id.id,
                                                                    "sale_product_id" : line.product_id.id
                                                                 }, context=context)
                        
                            for commisson_line in commission_lines:
                                period_ids.add(commisson_line["period_id"])
                                salesman_ids.add(commisson_line["partner_id"])
                                
                                commission_line_id = commission_line_obj.search_id(cr, uid, [("invoice_line_id", "=", commisson_line["invoice_line_id"]),
                                                                                          ("partner_id", "=", commisson_line["partner_id"]),
                                                                                          ("product_id","=", commisson_line["product_id"])], context=context)
                                                                                           
                                if commission_line_id:
                                    commission_line_obj.write(cr, uid, commission_line_id, commisson_line, context=context)                                
                                else:
                                    commission_line_obj.create(cr, uid, commisson_line, context=context)
                            
                        
                        # order based
                        cr.execute("SELECT sl.salesman_id, o.id FROM sale_order_line_invoice_rel rel  "
                                   " INNER JOIN sale_order_line sl ON sl.id = rel.order_line_id "
                                   " INNER JOIN sale_order o ON o.id = sl.order_id "
                                   " WHERE      rel.invoice_id = %s " 
                                   "       AND  sl.salesman_id IS NOT NULL "
                                   "       AND  o.pricelist_id IS NOT NULL "
                                   " GROUP BY 1,2 ", (line.id,))
                       
                        for salesman_id, order_id in cr.fetchall():
                            salesman_user = user_obj.browse(cr, uid, salesman_id, context=context)
                            order = order_obj.browse(cr, uid, order_id, context=context)     
                            commission_date = order.date_order                      
                            create_commission(salesman_user, name=order.name, commission_date=order.date_order, ref=order.name, pricelist=order.pricelist_id)
                            
                        # contract based
                        salesman_user = analytic_account.salesman_id
                        if salesman_user and not line.sale_order_line_ids:
                            create_commission(salesman_user)
        
        period_ids = list(period_ids)
        salesman_ids = list(salesman_ids)        
        commission_line_obj._update_bonus(cr, uid, salesman_ids, period_ids, context=context)
        
    
    def action_cancel(self, cr, uid, ids, context=None):
        ids_tuple=tuple(ids)
        
        cr.execute("SELECT sl.salesman_id FROM sale_order_line_invoice_rel rel  "
                   " INNER JOIN sale_order_line sl ON sl.id = rel.order_line_id "
                   " INNER JOIN sale_order o ON o.id = sl.order_id "
                   " WHERE      rel.invoice_id = %s " 
                   "       AND  sl.salesman_id IS NOT NULL " 
                   " GROUP BY 1 ", (ids_tuple,))
        
        salesman_ids = [r[0] for r in cr.fetchall()]
        
        cr.execute("SELECT inv.period_id FROM account_invoice inv"
                   " WHERE inv.id IN %s " 
                   " GROUP BY 1 ", (ids_tuple,))
                
        period_ids = [r[0] for r in cr.fetchall()]
        
        res = super(account_invoice,self).action_cancel(cr, uid, ids, context=context)        
        commission_line_obj = self.pool.get("commission.line")
        commission_line_obj._update_bonus(cr, uid, salesman_ids, period_ids, context=context)
        return res
        
    def action_move_create(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).action_move_create(cr, uid, ids, context=context)
        self._calc_sale_commission(cr, uid, ids, context=context)
        return res
  
    
    _inherit = "account.invoice"
