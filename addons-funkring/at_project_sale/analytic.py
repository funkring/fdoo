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
from openerp.addons.at_base import util

from dateutil.relativedelta import relativedelta

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
            if not ids:
                res["value"]["recurring_prepaid"] = template.recurring_prepaid

        return res
    
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
                                     domain="['|', ('section_id', '=', section_id), ('section_id', '=', False), ('object_id.model', '=', 'crm.lead')]", context="{'object_name': 'crm.lead'}")
    }
