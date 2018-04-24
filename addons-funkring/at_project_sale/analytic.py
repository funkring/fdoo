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

from openerp.osv import osv,fields
from openerp.exceptions import Warning
from openerp.addons.at_base import util
from openerp.addons.at_base import format
from openerp.addons.at_base import helper
from openerp.tools.translate import _

from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class account_analytic_account(osv.osv):    
    
    def name_get(self, cr, uid, ids, context=None):
        ids = util.idList(ids)
        res = super(account_analytic_account,self).name_get(cr,uid,ids,context=context)        
        if ids:
            cr.execute("SELECT a.id, p.name FROM account_analytic_account AS a "
                       " INNER JOIN res_partner AS p ON p.id = a.partner_id "
                       " WHERE a.id IN %s",
                       (tuple(ids),))
            
            partner_names = {}            
            for row in cr.fetchall():
                partner_names[row[0]] = row[1]            
                
            new_res = []
            for value in res:
                cur_id = value[0]
                cur_name = value[1]                
                name = partner_names.get(cur_id)                
                if name:
                    new_res.append((cur_id,cur_name + " [" + name + "]"))                    
                else:
                    new_res.append(value)
                       
            return new_res                 
        return res
      
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):        
        res = super(account_analytic_account,self).name_search(cr,uid,name,args=args,operator=operator,context=context,limit=limit)   
        if not res:
            account_ids = self.search(cr, uid, [("partner_id.name", operator, name)], limit=limit, context=context)
            if account_ids:
                return self.name_get(cr, uid, account_ids, context=context)
                        
            order_res = self.pool.get("sale.order").name_search(cr,uid,name,args=None,operator=operator,context=context,limit=limit)
            res = []
            if order_res:
                ids = [x[0] for x in order_res]
                analytic_id_for_order = {}
                cr.execute("SELECT id,project_id FROM sale_order WHERE id IN %s AND project_id IS NOT NULL",(tuple(ids),))                
                for row in cr.fetchall():
                    analytic_id_for_order[row[0]]=row[1]                    
                for tup in order_res:
                    analytic_id = analytic_id_for_order.get(tup[0])
                    if analytic_id:
                        res.append((analytic_id,tup[1]))
        return res
    
    def on_change_template(self, cr, uid, ids, template_id, date_start=False, context=None):
        res = super(account_analytic_account, self).on_change_template(cr, uid, ids, template_id, date_start=date_start, context=context)
        
        if template_id:
            template = self.browse(cr, uid, template_id, context=context)
            values = res["value"]
            if not ids:
                # take shop
                shop = template.shop_id
                if shop:
                  values["shop_id"] = shop.id
              
                # overtake prepaid
                values["recurring_prepaid"] = template.recurring_prepaid
                recurring_task_obj = self.pool("account.analytic.recurring.task")
                
                # overtake recurring task values
                recurring_task_vals = []
                for recurring_task in template.recurring_task_ids:
                  recurring_task_copy = recurring_task_obj.copy_data(cr, uid, recurring_task.id, context=context)
                  del recurring_task_copy["analytic_account_id"]
                  recurring_task_vals.append((0, 0, recurring_task_copy))
                  
                values["recurring_task"] = template.recurring_task
                values["recurring_task_interval"] = template.recurring_task_interval
                values["recurring_task_rule"] = template.recurring_task_rule
                values["recurring_task_ids"] = recurring_task_vals

        return res
      
    def unlink(self, cr, uid, ids, context=None):
        # unlink project if it is contract
        project_obj = self.pool.get('project.project')
        for account in self.browse(cr, uid, ids, context=context):
          if account.is_contract:            
            project_ids = project_obj.search(cr, uid, [('analytic_account_id','in',ids)])
            if project_ids:
              project_obj.unlink(cr, uid, project_ids, context=context)
        return super(account_analytic_account, self).unlink(cr, uid, ids, context=context)

    
    def _prepare_invoice_data(self, cr, uid, contract, context=None):
        invoice = super(account_analytic_account, self)._prepare_invoice_data(cr, uid, contract, context=context)
        
        # invoice name to contract name
        invoice["name"] = contract.name
        
        # determine user
        user_id = contract.manager_id or contract.user_id
        if user_id:
            invoice["user_id"] = user_id.id
        
        # determine shop
        if contract.shop_id:
            invoice["shop_id"] = contract.shop_id.id
        else:
            # shop from template
            template = contract.template_id
            if template and template.shop_id:
                invoice["shop_id"] = template.shop_id.id
            else:
                parent = contract.parent_id
                if parent:
                    # get shop from parent
                    if parent.shop_id:
                        invoice["shop_id"] = parent.shop_id.id
                    else:
                        # shop from autocreate
                        shop_obj = self.pool["sale.shop"]
                        shop_ids = shop_obj.search(cr, uid, [("autocreate_order_parent_id","=",parent.id)], limit=2)
                        if not shop_ids:
                            shop_ids = shop_obj.search(cr, uid, [("project_id","=",parent.id)], limit=2)
                        # check if only one shop is assinged
                        if len(shop_ids) == 1:
                            invoice["shop_id"] = shop_ids[0]
                        
        # performance period
        if contract.recurring_invoices:
            
            # get next date function            
            def getNextDate(cur_date,sign=1):
                interval = contract.recurring_interval*sign
                if contract.recurring_rule_type == 'daily':
                    return cur_date+relativedelta(days=+interval)
                elif contract.recurring_rule_type == 'weekly':
                    return cur_date+relativedelta(weeks=+interval)
                elif contract.recurring_rule_type == 'monthly':
                    return cur_date+relativedelta(months=+interval)
                else:
                    return cur_date+relativedelta(years=+interval)
            
            
            cur_date = util.strToDate(contract.recurring_next_date or util.currentDate())
            if contract.recurring_prepaid:
                invoice["perf_enabled"] = True
                invoice["perf_start"] = cur_date
                invoice["perf_end"] = getNextDate(cur_date)
            else:
                invoice["perf_enabled"] = True
                invoice["perf_start"] = getNextDate(cur_date,-1)
                invoice["perf_end"] = cur_date
                
            # first of month and last of month
            if contract.recurring_rule_type == 'monthly':
                invoice["perf_end"] = util.strToDate(util.getEndOfMonth(invoice["perf_end"]))
                if contract.recurring_interval > 0:
                    interval = -(contract.recurring_interval-1)
                    invoice["perf_start"] = util.strToDate(util.getFirstOfMonth(invoice["perf_end"]))+relativedelta(months=interval)
                
            # convert dt to str
            invoice["perf_start"] = util.dateToStr(invoice["perf_start"])
            invoice["perf_end"] = util.dateToStr(invoice["perf_end"])

        return invoice
    
    def _root_account(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            parent = obj.parent_id            
            if parent:
                while parent.parent_id:
                    parent = parent.parent_id
                res[obj.id] = parent.id
        return res
    
    def _relids_account(self, cr, uid, ids, context=None):
        res = self.search(cr, uid, [("id","child_of",ids)], context=context)
        return res
    
    def onchange_recurring_task(self, cr, uid, ids, recurring_task, date_start=False, context=None):
        if date_start and recurring_task:
            return {'value': {'recurring_task_next': date_start}}
        return {}
    
    def recurring_task_create(self, cr, uid, ids, context=None):
        return self._recurring_task_create(cr, uid, ids, context=context)
   
    def _cron_recurring_task_create(self, cr, uid, context=None):
        return self._recurring_task_create(cr, uid, [], automatic=True, context=context)

    def _recurring_task_prepare(self, cr, uid, project, recurring_task, interval_name, next_date, context=None):
        name = "%s %s" % (recurring_task.name, interval_name)
        values = {
          "name": name,
          "description": recurring_task.description,
          "project_id": project.id,
          "planned_hours": recurring_task.planned_hours,
          "sequence": recurring_task.sequence,
          "date_deadline": util.getPrevDayDate(next_date),          
        }
        product = recurring_task.product_id
        if product:
          values["inv_product_id"] = product.id
        return values

    def _recurring_task_create(self, cr, uid, ids, automatic=False, context=None):
        if context is None:
          context = {}
          
        task_ids = []
        
        current_date =  util.currentDate()
        if ids:
            contract_ids = ids
        else:
            contract_ids = self.search(cr, uid, [("use_tasks","=",True), ("recurring_task_next","<=", current_date), ("state","=", "open"), ("recurring_task","=", True), ("type", "=", "contract")])
        if contract_ids:
            
            task_obj = self.pool["project.task"]
            recurring_task_obj = self.pool["account.analytic.recurring.task"]
            project_obj = self.pool["project.project"]
            f = format.LangFormat(cr, uid, context)
            
            cr.execute("SELECT company_id, array_agg(id) as ids FROM account_analytic_account WHERE id IN %s GROUP BY company_id", (tuple(contract_ids),))
            for company_id, ids in cr.fetchall():
                context_contract = dict(context, company_id=company_id, force_company=company_id)
                for contract in self.browse(cr, uid, ids, context=context_contract):
                    
                    project_ids = project_obj.search(cr, uid, [("analytic_account_id","=",contract.id)], context=context_contract)
                    if not project_ids:
                      raise Warning(_("No Project for generating tasks of contract %s found") % contract.name)
                    
                    project = project_obj.browse(cr, uid, project_ids[0], context=context_contract)
                    
                    try:
                      
                        # get interval
                        interval = contract.recurring_task_interval
                        rule = contract.recurring_rule_type      
                        next_date = contract.recurring_task_next or current_date                
                        if contract.recurring_task_rule == "daily":
                          # daily
                          dt_interval = relativedelta(days=interval)
                          interval_name = f.formatLang(next_date, date=True)
                        elif contract.recurring_task_rule == "weekly":
                          # weekly
                          dt_interval = relativedelta(weeks=interval)
                          interval_name = _("%s WE%s") % (util.getYearStr(next_date), util.getWeek(next_date))
                        elif contract.recurring_task_rule == "monthly":
                          # monthly
                          dt_interval = relativedelta(months=interval)
                          interval_name = helper.getMonthYear(cr, uid, next_date, context=context)
                        else:
                          # yearly
                          interval_name = util.getYearStr(next_date)
                          dt_interval = relativedelta(years=interval)
                        
                        # next date
                        next_date = util.dateToStr(util.strToDate(next_date) + dt_interval)
                        
                        # execute task
                        processed_tasks = 0
                        finished_tasks = 0
                        for recurring_task in contract.recurring_task_ids:
                          
                          task_values = self._recurring_task_prepare(cr, uid, project, recurring_task, interval_name, next_date, context=context_contract)
                          if task_values:
                            
                            processed_tasks += 1
                            
                            # execute task if it is not finished
                            task_count = recurring_task.count
                            if not recurring_task.repeat or task_count < recurring_task.repeat:
                              task_count = recurring_task.count + 1                          
                              task_ids.append(task_obj.create(cr, uid, task_values, context=context_contract))
                              recurring_task_obj.write(cr, uid, [recurring_task.id], {"count": task_count}, context=context_contract)
                              
                            # check if task is finished
                            if recurring_task.repeat and task_count >= recurring_task.repeat:
                              finished_tasks += 1                      
                          
                        # check if all tasks are finished  
                        if finished_tasks and finished_tasks == processed_tasks:
                          values["recurring_task"] = False

                        # update contract
                        values = {"recurring_task_next": next_date}
                        self.write(cr, uid, [contract.id], values, context=context)
                        
                        # commit if automatic 
                        if automatic:
                            cr.commit()
                            
                    except Exception:
                        # log error if automatic
                        if automatic:
                            cr.rollback()
                            _logger.exception("Fail to create recurring task for contract %s [%s]", (contract.name, contract.code))
                        else:
                            raise
                          
        return task_ids

    
    _inherit = "account.analytic.account"    
    _columns = {
        "order_id" : fields.many2one("sale.order", "Order", ondelete="cascade", copy=False, select=True),
        "shop_id" : fields.many2one("sale.shop", "Shop", select=True),
        "recurring_prepaid" : fields.boolean("Prepaid"),
        "root_account_id" : fields.function(_root_account, type="many2one", obj="account.analytic.account", string="Root", select=True, store={
            "account.analytic.account" : (_relids_account, ["parent_id"], 10)
        }),
        "is_contract": fields.boolean("Contract"),
        "section_id": fields.related("order_id", "section_id", type="many2one", relation="crm.case.section", string="Sales Team"),
        "categ_ids" : fields.related("order_id", "categ_ids", type="many2many", relation="crm.case.categ", string="Tags",
                                     domain="['|', ('section_id', '=', section_id), ('section_id', '=', False), ('object_id.model', '=', 'crm.lead')]", context="{'object_name': 'crm.lead'}"),
               
        "recurring_task": fields.boolean("Recurring Tasks"),
        "recurring_task_ids": fields.one2many("account.analytic.recurring.task", "analytic_account_id", "Recurring Tasks", copy=True),
        "recurring_task_rule": fields.selection([
              ("daily", "Day(s)"),
              ("weekly", "Week(s)"),
              ("monthly", "Month(s)"),
              ("yearly", "Year(s)")], "Task Recurrency", help="Task automatically repeat at specified interval"),
        "recurring_task_interval": fields.integer("Repeat Task Every", help="Repeat every (Days/Week/Month/Year)"),
        "recurring_task_next":  fields.date("Date of Next Task(s)"),
    }
    _defaults = {
        "recurring_task_interval": 1,
        "recurring_task_next": lambda *a: util.currentDate(),
        "recurring_task_rule": "monthly"
    }
    
  
class account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'
    
    def invoice_cost_create(self, cr, uid, ids, data=None, context=None):      
      if not data or (not data.get("product_id") and not data.get("inv_task_product_group")):
        inv_ids = []
        
        if data is None:
          data = {}
        
        cr.execute(""" SELECT l.id, t.inv_product_id  FROM account_analytic_line l 
                       LEFT JOIN hr_analytic_timesheet hr ON hr.line_id = l.id
                       LEFT JOIN project_task_work w ON w.hr_analytic_timesheet_id = hr.id 
                       LEFT JOIN project_task t ON t.id = w.task_id  
                       WHERE l.id IN %s """, (tuple(ids),))
        
        # group
        byProduct = {}
        for line_id, inv_product_id in cr.fetchall():
          inv_product_id = inv_product_id or 0
          line_ids = byProduct.get(inv_product_id, None)
          if line_ids is None:
            line_ids = []
            byProduct[inv_product_id] = line_ids
          line_ids.append(line_id)
          
        # create invoices
        for inv_product_id, line_ids in byProduct.iteritems():
          inv_data = dict(data)
          inv_data["inv_task_product_group"] = True
          if inv_product_id:
            inv_data["product"] = inv_product_id
          inv_ids.extend(self.invoice_cost_create(cr, uid, line_ids, inv_data, context=context))
          
        return inv_ids
        
      return super(account_analytic_line, self).invoice_cost_create(cr, uid, ids, data=data, context=context)
    
    
class analytic_recurring_task(osv.osv):
    _name = "account.analytic.recurring.task"
    _description = "Recurring Task"
    _columns = {
      "analytic_account_id": fields.many2one("account.analytic.account", "Analytic Account", required=True),
      "name": fields.char("Name"),
      "description": fields.text("Description"),
      "planned_hours": fields.float("Planned Hours"),
      "product_id": fields.many2one("product.product", "Product", help="Product for invoicing"),
      "sequence": fields.integer("Sequence"),
      "repeat": fields.integer("Repeat", help="0 for repeat infinitely, 1 for create task only once, 2 for create task only twice, ..."),
      "count": fields.integer("Count", readonly=True, copy=False, help="Amount of created task by this rule")      
    }
    _defaults = {
      "sequence": 10
    }
        
    def onchange_product(self, cr, uid, ids, product_id, company_id, context=None):
      values = {}
      if product_id:
        product = self.pool["product.product"].browse(cr, uid, product_id, context=context)
        if product:
          values["name"] = product.name
          values["planned_hours"] = product.planned_hours
          description = product.description_sale
          if description:
            values["description"] = description
      return  {"value": values}

