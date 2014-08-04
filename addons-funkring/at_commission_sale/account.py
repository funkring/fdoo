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

from openerp.osv import osv
from openerp.tools.translate import _

class account_invoice(osv.osv):
    
    def _calc_sale_commission(self, cr, uid, ids, context=None):   
        """ Create Analytic lines for invoice """        
        period_ids = set()
        salesman_ids = set()
        #
        user_obj = self.pool.get("res.users")
        pricelist_obj = self.pool.get("product.pricelist")
        pricelist_item_obj = self.pool.get("product.pricelist.item")
        commission_line_obj = self.pool.get("at_commission.line")
        invoice_obj = self.pool.get("account.invoice")
        order_obj = self.pool.get("sale.order")
        period_obj = self.pool.get("account.period")
        #        
        for invoice in self.browse(cr, uid, ids, context=context):                       
            #
            company = invoice.company_id
            if company.commission_type == "invoice" or invoice.type in ("out_refund","in_invoice"):
                #
                sign = -1
                if invoice.type in ("out_invoice", "in_refund"):
                    sign = 1
                #                   
                for line in invoice.invoice_line:
                    product = line.product_id
                    analytic_account = line.account_analytic_id
                    if analytic_account and product:     
                        
                        cr.execute("SELECT sl.salesman_id, o.id, o.pricelist_id FROM sale_order_line_invoice_rel rel  "
                                   " INNER JOIN sale_order_line sl ON sl.id = rel.order_line_id "
                                   " INNER JOIN sale_order o ON o.id = sl.order_id "
                                   " WHERE      rel.invoice_id = %s " 
                                   "       AND  sl.salesman_id IS NOT NULL "
                                   "       AND  o.pricelist_id IS NOT NULL "
                                   " GROUP BY 1,2,3 ", (line.id,))
                       
                        for row in cr.fetchall():
                            salesman_user = user_obj.browse(cr,uid,row[0],context)                            
                            #
                            order_id = row[1]
                            pricelist_id = row[2]
                            #
                            partner = salesman_user.partner_id
                            order = order_obj.browse(cr,uid,order_id,context)
                            team = salesman_user.context_section_id
                            if team and partner:
                                item_id = pricelist_obj.price_get(cr,uid,[pricelist_id],product.id,line.quantity,
                                                                  partner=invoice.partner_id.id,context=context)["item_id"][pricelist_id]
                                
                                percent = item_id and pricelist_item_obj.browse(cr,uid,item_id,context).commission or 0.0
                                if not percent:
                                    percent = team.sales_commission
                                    
                                if percent:
                                    commission_date = order.date_order or invoice.date_invoice
                                    period_id = period_obj.find_period_id(cr,uid,commission_date) or invoice.period_id.id                                    
                                    #       
                                    salesman_ids.add(salesman_user.id)
                                    period_ids.add(period_id)
                                    #
                                    subtotal = line.price_subtotal*sign
                                    ref = invoice_obj.invoice_ref(cr,uid,invoice)
                                    commission_product = team.property_commission_product
                                    journal = team.property_analytic_journal
                                    amount = commission_line_obj._get_sale_commission(cr,uid,subtotal,percent,context=context)
                                    #                            
                                    values = {
                                        "invoice_id" : invoice.id,
                                        "name": _("Sales Commission: %s") % (line.name,),
                                        "date": commission_date,
                                        "account_id": analytic_account.id,
                                        "unit_amount": line.quantity,
                                        "amount": amount,
                                        "base_commission" : percent,   
                                        "total_commission" : percent,                             
                                        "product_id": commission_product.id,
                                        "product_uom_id": commission_product.uom_id.id,
                                        "general_account_id": commission_product.account_income_standard_id.id,
                                        "journal_id": journal.id,
                                        "salesman_id" : salesman_user.id,
                                        "partner_id" : partner.id,
                                        "invoice_line_id" : line.id,
                                        "user_id" : uid,
                                        "ref": order.name or ref or None,
                                        "sale_partner_id" : invoice.partner_id.id,
                                        "sale_product_id" : line.product_id.id,
                                        "period_id" : period_id,
                                        "price_sub" : subtotal
                                    }
                                    commission_line_ids = commission_line_obj.search(cr, uid, [("invoice_line_id", "=", line.id), ("partner_id", "=", partner.id)])
                                    commission_line_id = commission_line_ids and commission_line_ids[0] or None
                                    #
                                    if not commission_line_id:
                                        commission_line_obj.create(cr, uid, values)
                                    elif commission_line_id and not commission_line_obj.browse(cr, uid, commission_line_id).invoiced_id:
                                        commission_line_obj.write(cr, uid, commission_line_id, values)    
        #        
        period_ids = list(period_ids)
        salesman_ids = list(salesman_ids)
        commission_line_obj._update_bonus(cr,uid,salesman_ids,period_ids)
        
    
    def action_cancel(self, cr, uid, ids, *args):
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
        
        res = super(account_invoice,self).action_cancel(cr,uid,ids,args)
        #
        commission_line_obj = self.pool.get("at_commission.line")
        commission_line_obj._update_bonus(cr,uid,salesman_ids,period_ids)
        return res

        
    def action_move_create(self, cr, uid, ids, *args):
        super(account_invoice,self).action_move_create(cr, uid, ids, *args)
        self._calc_sale_commission(cr, uid, ids)
  
    
    _inherit = "account.invoice"
account_invoice()
