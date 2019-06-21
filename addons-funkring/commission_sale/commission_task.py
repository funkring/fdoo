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
    taskc.substage("Sale Commission")
    
    taskc.stage(_("Order based"))
    self._calc_sale_commission_order(taskc)    
    taskc.done()
    
    taskc.stage(_("Invoice based"))
    self._calc_sale_commission_invoice(taskc)    
    taskc.done()
    
    taskc.done()
  
  @api.model
  def _commission_sale(self, order, context=None):
    res = []
    
    analytic_account = order.project_id
    commission_obj = self.env["commission.line"]
    
    for line in order.order_line:
      product = line.product_id
      if product:      
          commission_lines = commission_obj._get_sale_commission(line.name, order.user_id, 
                                                   order.partner_id, 
                                                   product, 
                                                   line.product_uos_qty, 
                                                   line.price_subtotal, 
                                                   date=order.date_order, 
                                                   pricelist=order.pricelist_id, 
                                                   defaults={
                                                      "ref": order.name,
                                                      "order_line_id": line.id,
                                                      "order_id": line.order_id.id,
                                                      "account_id": analytic_account.id,
                                                      "sale_partner_id": order.partner_id.id,
                                                      "sale_product_id": line.product_id.id,
                                                      "task_id": self.id
                                                   },
                                                   obj=line,
                                                   company=order.company_id,
                                                   commission_custom=line.commission_custom or None,                    
                                                   context=context)
          res.extend(commission_lines)
    return res


  def _calc_sale_commission_order(self, taskc):
    domain = [("state", "not in", ["draft","cancel","sent"])]
    if self.user_id:
      domain.append(("user_id","=",self.user_id.id))
                     
    if self.date_from: 
      domain.append(("date_order", ">=", self.date_from))
      
    if self.date_to:
      domain.append(("date_order", "<=", self.date_to))              
      
    orders = self.env["sale.order"].search(domain)
    
    commission_obj = self.env["commission.line"]
    period_ids = set()
    salesman_ids = set()
    
    taskc.substage("(Re)Calc orders")
    taskc.initLoop(len(orders))    
    
    for order in orders:
      taskc.nextLoop()
      
      company = order.company_id 
      analytic_account = order.project_id
      
      if company.commission_type == "order" and analytic_account:
        commission_lines = self._commission_sale(order)
        for commission_line in commission_lines:
          period_ids.add(commission_line["period_id"])
          salesman_ids.add(commission_line["salesman_id"])
          
          commission = commission_obj.search([("order_id", "=", commission_line["order_id"]),
                                              ("order_line_id", "=", commission_line["order_line_id"]),                                                                           
                                              ("partner_id", "=", commission_line["partner_id"]),
                                              ("product_id","=", commission_line["product_id"]),
                                              ("val_based","=", commission_line.get("val_based",False))])
          
          if commission:
            if len(commission) > 1:
              taskc.loge(_("Unable to update commission! There exist more commissions of same type"), ref="sale.order.line,%s" % commission_line["order_line_id"])
              continue
            if commission.invoice_id:
              taskc.loge(_("Commission was already invoiced and cannot be regenerated"), ref="sale.order.line,%s" % commission_line["order_line_id"])
              continue
            # update commission
            commission.write(commission_line)
          else:
            # create new
            commission.create(commission_line)
                                                   
    taskc.done()
    
    taskc.log("Update bonus")
    period_ids = list(period_ids)
    salesman_ids = list(salesman_ids)
    commission_obj._update_bonus(salesman_ids, period_ids)
  
  @api.model  
  def _recalc_invoices(self, domain, force=False, taskc=None):
    if not taskc:
      taskc = TaskLogger(__name__)
    
    period_ids = set()
    salesman_ids = set()
        
    user_obj = self.env["res.users"]
    commission_obj = self.env["commission.line"]
    order_obj = self.env["sale.order"]
    cr = self._cr
             
    invoices = self.env["account.invoice"].search(domain)
    
    taskc.substage("(Re)Calc invoies")           
    taskc.initLoop(len(invoices))  
             
    for invoice in invoices:
      company = invoice.company_id
      if company.commission_type == "invoice" or (force and invoice.type in ("out_refund","in_invoice")):
    
          sign = 1
          # change sign on in invoice or out refund
          if invoice.type in ("in_invoice", "out_refund"):
              sign = -1
    
          for line in invoice.invoice_line:
              product = line.product_id
              if product:     
              
                  analytic_account = line.account_analytic_id    
                  default_analytic_account = analytic_account
                  if not analytic_account:
                      default_analytic_account = invoice.shop_id.project_id
                      
                  if not default_analytic_account:
                      raise Warning(_("No analytic account for commission found!"))
                      
                  def create_commission(salesman_user, commission_date=None, ref=None, pricelist=None):
                      price_subtotal = sign*line.price_subtotal              
                      
                      commission_defaults = {
                          "ref" : ref or invoice.number,
                          "invoice_line_id" : line.id,
                          "sale_partner_id" : invoice.partner_id.id,
                          "sale_product_id" : line.product_id.id,
                          "account_id" : default_analytic_account.id,
                          "task_id": self.id
                      }
                      
                      commission_lines = commission_obj._get_sale_commission(line.name, salesman_user, 
                                                           invoice.partner_id, 
                                                           product, 
                                                           line.quantity, 
                                                           price_subtotal, 
                                                           date=commission_date or invoice.date_invoice, 
                                                           pricelist=pricelist,
                                                           defaults=commission_defaults,
                                                           company=company,
                                                           obj=line)
                  
                      has_commission = False
                      for commission_line in commission_lines:
                          period_ids.add(commission_line["period_id"])
                          salesman_ids.add(commission_line["salesman_id"])
                          
                          commission = commission_obj.search([("invoice_line_id", "=", commission_line["invoice_line_id"]),
                                                              ("partner_id", "=", commission_line["partner_id"]),
                                                              ("product_id","=", commission_line["product_id"]),
                                                              ("val_based","=", commission_line.get("val_based",False))])
          
                          if commission:
                            if len(commission) > 1:
                              taskc.loge(_("Unable to update commission! There exist more commissions of same type"), ref="account.invoice.line,%s" % commission_line["invoice_line_id"])
                              continue
                            if commission.invoice_id:
                              taskc.loge(_("Commission was already invoiced and cannot be regenerated"), ref="account.invoice.line,%s" % commission_line["invoice_line_id"])
                              continue
                            # update commission
                            commission.write(commission_line)
                            has_commission = True
                          else:
                            # create new
                            commission.create(commission_line)
                            has_commission = True
                          
                      return has_commission 
                      
                  
                  # order based
                  user_id = None
                  if sign > 0:
                      cr.execute("SELECT o.user_id, o.id FROM sale_order_line_invoice_rel rel  "
                                 " INNER JOIN sale_order_line sl ON sl.id = rel.order_line_id "
                                 " INNER JOIN sale_order o ON o.id = sl.order_id "
                                 " WHERE      rel.invoice_id = %s " 
                                 "       AND  o.user_id IS NOT NULL "
                                 "       AND  o.pricelist_id IS NOT NULL "
                                 " GROUP BY 1,2 ", (line.id,))
                     
                      # search order based
                      for salesman_id, order_id in cr.fetchall():
                          salesman_user = user_obj.browse(salesman_id)
                          order = order_obj.browse(order_id)     
                          if create_commission(salesman_user, commission_date=invoice.date_invoice, ref=order.name, pricelist=order.pricelist_id):
                              user_id = salesman_id
                              break
                      
                      # fallback invoice based
                      if not user_id:
                        if create_commission(invoice.user_id, commission_date=invoice.date_invoice, ref=invoice.origin):
                          user_id = invoice.user_id.id
                      
                  # invoice based (refund)
                  else:                            
                      # order based
                      if analytic_account:
                          order = order_obj.with_context(active_test=False).search([("project_id","=",analytic_account.id)], limit=2)
                          if len(order) == 1:
                              if create_commission(order.user_id, commission_date=invoice.date_invoice, ref=order.name, pricelist=order.pricelist_id):
                                  user_id = order.user_id.id
                                  
                      # fallback invoice based
                      if not user_id and create_commission(invoice.user_id, commission_date=invoice.date_invoice, ref=invoice.origin):
                        user_id = invoice.user_id.id
                      
                  # contract based
                  if analytic_account:
                    salesman_user = analytic_account.salesman_id
                    if salesman_user and not line.sale_order_line_ids and (not user_id or user_id != salesman_user.id):
                      create_commission(salesman_user)
        
    taskc.done()
    
    taskc.log("Update bonus")
    period_ids = list(period_ids)
    salesman_ids = list(salesman_ids)        
    commission_obj._update_bonus(salesman_ids, period_ids)
  
  def _calc_sale_commission_invoice(self, taskc=None):
    if not taskc:
      taskc = TaskLogger(__name__)
    
    domain = [("state", "!=", "draft"),("state", "!=", "cancel")]  
    if self.user_id:
      domain.append(("user_id","=",self.user_id.id))
                     
    if self.date_from: 
      domain.append(("date_invoice", ">=", self.date_from))
      
    if self.date_to:
      domain.append(("date_invoice", "<=", self.date_to))              
      
    self._recalc_invoices(domain, taskc=taskc, force=True)
   
