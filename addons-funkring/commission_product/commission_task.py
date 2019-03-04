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

from openerp import models, api, _
from openerp.addons.automation.automation import TaskLogger

class commission_task(models.Model):
  _inherit = "commission.task"

  def _run_options(self):
    res = super(commission_task, self)._run_options()
    res["stages"] += 1
    return res
  
  @api.one  
  def _run(self, taskc):
    taskc.substage("Product Commission")
    
    taskc.stage(_("Order based"))
    self._calc_product_commission_order(taskc)    
    taskc.done()
    
    taskc.stage(_("Invoice based"))
    self._calc_product_commission_invoice(taskc)    
    taskc.done()
    
    taskc.done()
    
  def _calc_product_commission_order(self, taskc):
    domain = [("state", "not in", ["draft","cancel","sent"])]    
    if self.user_id:
      domain.append(("user_id","=",self.user_id.id))
                     
    if self.date_from: 
      domain.append(("date_order", ">=", self.date_from))
      
    if self.date_to:
      domain.append(("date_order", "<=", self.date_to))              
      
    orders = self.env["sale.order"].search(domain)
    
    commission_obj = self.env["commission.line"]
    
    taskc.substage("(Re)Calc orders")
    taskc.initLoop(len(orders))    
    
    for order in orders:
      taskc.nextLoop()
      
      company = order.company_id 
      analytic_account = order.project_id
      if company.commission_type == "order" and analytic_account:
        for line in order.order_line:
          if line.product_id:
            commission_lines = commission_obj._get_product_commission(line.name, 
                                         line.product_id, 
                                         line.product_uos_qty, 
                                         line.price_subtotal, 
                                         order.date_order,
                                         defaults= {
                                            "account_id": analytic_account.id,
                                            "order_id": line.order_id.id,
                                            "order_line_id" : line.id,
                                            "ref": order.name,
                                            "sale_partner_id" : order.partner_id.id,
                                            "sale_product_id" : line.product_id.id,
                                            "task_id": self.id
                                         },
                                         obj=line,
                                         company=company)  
            
            for commission_line in commission_lines:
              commission = commission_obj.search([("order_line_id", "=", line.id), 
                                                  ("product_id", "=", commission_line["product_id"]),
                                                  ("partner_id", "=", commission_line["partner_id"])])
              
              if commission:
                if len(commission) > 1:
                  taskc.loge(_("Unable to update product commission! There exist more commissions of same type"), ref="sale.order.line,%s" % commission_line["order_line_id"])
                  continue
                if commission.invoice_id:
                  taskc.loge(_("Product commission was already invoiced and cannot be regenerated"), ref="sale.order.line,%s" % commission_line["order_line_id"])
                  continue
                # update commission
                commission.write(commission_line)
              else:
                # create new
                commission.create(commission_line)
                
      taskc.done()
                
    @api.model  
    def _recalc_invoices(self, domain, force=False, taskc=None):
      if not taskc:
        taskc = TaskLogger(__name__)
      
      commission_obj = self.env["commission.line"]

      invoices = self.env["account.invoice"].search(domain)    
      
      taskc.substage("(Re)Calc invoices")
      taskc.initLoop(len(orders))    
      
      for invoice in invoices:
        taskc.nextLoop()
        
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
                        
                    commission_lines = commission_obj._get_product_commission(line.name, 
                                           product,
                                           line.quantity,
                                           price_subtotal,
                                           commission_date,
                                           defaults={
                                             "account_id" : analytic_account.id,
                                             "invoice_line_id" : line.id,
                                             "ref": ":".join(order_names) or ref or None,
                                             "sale_partner_id" : invoice.partner_id.id,
                                             "sale_product_id" : line.product_id.id,
                                             "task_id": self.id
                                           },
                                           obj=line,
                                           company=company)
                    
                    for commission_line in commission_lines:
                        commission = commission_obj.search([("invoice_line_id", "=", line.id), 
                                                            ("partner_id", "=", commission_line["partner_id"]),
                                                            ("product_id", "=", commission_line["product_id"])])
                        
                        if commission:
                          if len(commission) > 1:
                            taskc.loge(_("Unable to update product commission! There exist more commissions of same type"), ref="account.invoice.line,%s" % commission_line["invoice_line_id"])
                            continue
                          if commission.invoice_id:
                            taskc.loge(_("Product commission was already invoiced and cannot be regenerated"), ref="account.invoice.line,%s" % commission_line["invoice_line_id"])
                            continue
                          # update commission
                          commission.write(commission_line)
                        else:
                          # create new
                          commission.create(commission_line)
        
      taskc.done()
            
    def _calc_product_commission_invoice(self, taskc):
      domain = [("state", "not in", ["draft","cancel","sent"])]    
      if self.user_id:
        domain.append(("user_id","=",self.user_id.id))
                       
      if self.date_from: 
        domain.append(("date_invoice", ">=", self.date_from))
        
      if self.date_to:
        domain.append(("date_invoice", "<=", self.date_to))              
        
      self._recalc_invoices(domain, force=True, taskc=taskc)
