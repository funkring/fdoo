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
        #
        user_obj = self.pool.get("res.users")
        pricelist_obj = self.pool.get("product.pricelist")
        pricelist_item_obj = self.pool.get("product.pricelist.item")
        commission_line_obj = self.pool.get("commission.line")
        invoice_obj = self.pool.get("account.invoice")
        order_obj = self.pool.get("sale.order")
        period_obj = self.pool.get("account.period")
        rule_obj = self.pool.get("commission_sale.rule")
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
                        
                        def create_commission(salesman_user, name=None, commission_date=None, ref=None, pricelist_id=None):
                            partner = salesman_user.partner_id                        
                            team = salesman_user.default_section_id
                            if team and partner:
                                # get global commission
                                percent = product.commission_percent or product.categ_id.commission_percent or team.sales_commission
                                # search for rule                                                               
                                rule = rule_obj._get_rule(cr, uid, team, product, context=context)
                                if rule:
                                    percent = rule.get("commission",0.0) or 0.0
                                elif pricelist_id:
                                    # search for pricelist rule
                                    item_id = pricelist_obj.price_rule_get(cr, uid, [pricelist_id], product.id, line.quantity,
                                                           partner=invoice.partner_id.id,context=context)[pricelist_id][1]
                                    
                                    if item_id:
                                        prule = pricelist_item_obj.read(cr, uid, item_id, ["commission_active","commission"], context=context)
                                        if prule.get("commission_active"):
                                            percent = prule.get("commission",0.0) or 0.0                                        
                                    
                                # only process if percent
                                if percent:
                                    if not commission_date:
                                        commission_date = invoice.date_invoice
                                    if not ref:
                                        ref = invoice.number
                                        
                                    period_id = period_obj.find_period_id(cr, uid, commission_date, context=context) or invoice.period_id.id                                    
                                           
                                    salesman_ids.add(salesman_user.id)
                                    period_ids.add(period_id)
                                    subtotal = line.price_subtotal*sign                                    

                                    commission_product = team.property_commission_product
                                    journal = team.property_analytic_journal
                                    amount = commission_line_obj._get_sale_commission(cr,uid,subtotal,percent,context=context)
                                    #                            
                                    values = {
                                        "invoice_id" : invoice.id,
                                        "name": _("Sales Commission: %s") % commission_line_obj._short_name(line.name),
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
                                        "ref": ref,
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
                        
                        
                        # order based
                        cr.execute("SELECT sl.salesman_id, o.id, o.pricelist_id FROM sale_order_line_invoice_rel rel  "
                                   " INNER JOIN sale_order_line sl ON sl.id = rel.order_line_id "
                                   " INNER JOIN sale_order o ON o.id = sl.order_id "
                                   " WHERE      rel.invoice_id = %s " 
                                   "       AND  sl.salesman_id IS NOT NULL "
                                   "       AND  o.pricelist_id IS NOT NULL "
                                   " GROUP BY 1,2,3 ", (line.id,))
                       
                        for salesman_id, order_id, pricelist_id in cr.fetchall():
                            salesman_user = user_obj.browse(cr, uid, salesman_id, context)
                            order = order_obj.browse(cr, uid, order_id, context)     
                            commission_date = order.date_order                      
                            create_commission(salesman_user, name=order.name, commission_date=order.date_order, ref=order.name, pricelist_id=pricelist_id)
                            
                        # contract based
                        salesman_user = analytic_account.salesman_id
                        if salesman_user and not line.sale_order_line_ids:
                            create_commission(salesman_user)
        
        period_ids = list(period_ids)
        salesman_ids = list(salesman_ids)
        commission_line_obj._update_bonus(cr,uid,salesman_ids,period_ids)
        
    
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
        #
        commission_line_obj = self.pool.get("commission.line")
        commission_line_obj._update_bonus(cr,uid,salesman_ids,period_ids)
        return res

        
    def action_move_create(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).action_move_create(cr, uid, ids, context=context)
        self._calc_sale_commission(cr, uid, ids, context=context)
        return res
  
    
    _inherit = "account.invoice"
