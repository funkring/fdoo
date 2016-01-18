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

from openerp.osv import fields,osv

from openerp.addons.at_base import util
from openerp.addons.at_base import format

from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID

class sale_shop(osv.osv):
    _inherit = "sale.shop"
    _columns = {
        "autocreate_order_parent_id": fields.many2one('account.analytic.account', 'Analytic account default parent', domain=[("type","=","view")]),
        "autocreate_order_analytic_account" : fields.boolean("Analytic Account per Order"),
        "project_template_id" : fields.many2one("project.project", "Project template")
    }

class sale_order(osv.osv):

    def _project_name_get(self,cr,uid,order_values):
        order_name = order_values.get("name","")
        client_order_ref = order_values.get("client_order_ref")
        if client_order_ref:
            return "%s / %s" % (order_name,client_order_ref)
        return order_name

#    TODO: For this Workflow has to be extended, that means
#          after finishing the shipping a manual invoice have to be started
#          of only service products and one product with auto_create_task are
#          contained
#
#     def test_no_product(self, cr, uid, order, context):
#         for line in order.order_line:
#             if line.state == "cancel":
#                 continue
#             product = line.product_id
#             if product and (product.type != 'service' or product.auto_create_task):
#                 return False
#         return True

    def _correct_analytic_values(self,cr,uid,order_id,vals,context=None):
        """ Sync analytic account and sale order

            :returns: analytic account id if a new one is created otherwise False is returned
        """
        def get_fkey(inDict,inKey):
            if inDict:
                res = inDict.get(inKey,None)
                if res:
                    return res[0]
            return None

        analytic_id = None
        order_values = {}

        if order_id:
            order_read = self.read(cr, uid, order_id, ["project_id","partner_id","pricelist_id","name","shop_id", "client_order_ref"], context)
            order_values["project_id"]=get_fkey(order_read,"project_id")
            order_values["partner_id"]=get_fkey(order_read,"partner_id")
            order_values["pricelist_id"]=get_fkey(order_read,"pricelist_id")
            order_values["client_order_ref"]=order_read.get("client_order_ref")
            order_values["name"]=order_read.get("name")
            order_values["shop_id"]=get_fkey(order_read,"shop_id")
            analytic_id = order_values.get("project_id")
        else:
            if not vals.get("name"):
                vals["name"]=self.default_get(cr, uid, ["name"], context)["name"]

        shop_id = vals.get("shop_id",order_values.get("shop_id",context.get("shop")))
        if shop_id:
            shop=self.pool.get("sale.shop").browse(cr, uid, shop_id,context=context)
            if shop.autocreate_order_analytic_account:
                # init order values
                order_values["partner_id"]=vals.get("partner_id",order_values.get("partner_id"))
                order_values["pricelist_id"]=vals.get("pricelist_id",order_values.get("pricelist_id"))
                order_values["name"]=vals.get("name",order_values.get("name"))
                order_values["client_order_ref"]=vals.get("client_order_ref",order_values.get("client_order_ref"))

                # init vars
                analytic_obj = self.pool.get("account.analytic.account")
                project_context=context.copy()
                project_vals = {}
                project_name = self._project_name_get(cr,uid,order_values)
                partner_id = order_values["partner_id"]
                pricelist_id = order_values["pricelist_id"]
              
                #init all and determine parent project
                shop_analytic_parent_id = shop.autocreate_order_parent_id.id
                parent_analytic = None

                # get parent project
                parent_analytic_id = context.get("parent_project_id",None)
                if parent_analytic_id:
                    parent_analytic = analytic_obj.browse(cr, uid, parent_analytic_id, context=context)
                elif analytic_id:
                    analytic = analytic_obj.browse(cr, uid, analytic_id, context=context)
                    parent_analytic = analytic.parent_id

                # check if parent is valid
                if parent_analytic:
                    # reset project parent if it has not an order id
                    if not parent_analytic.order_id:
                        parent_analytic = None
                    else:
                        #reset parent_analytic if parent_analytic shop is not the same
                        #as the shop now
                        shop_obj = self.pool.get("sale.shop")
                        parent_shop_id = shop_obj.search_id(cr,uid,[("autocreate_order_parent_id","=",parent_analytic.id)])
                        if parent_shop_id and parent_shop_id != shop_id:
                            parent_shop_id=None

                # check for partner project
                if partner_id:
                    partner = self.pool.get("res.partner").browse(cr,uid,partner_id)
                    partner_account = partner.property_partner_analytic_account
                    if partner_account:
                        parent_analytic = partner_account

                # set values, these values are only written
                # if project exists or a new one is created
                project_vals["parent_id"]=(parent_analytic and parent_analytic.id) or shop_analytic_parent_id
                project_vals["code"]=order_values.get("name")
                project_vals["order_id"]=order_id
                project_vals["name"]=project_name
                project_context['default_name']=project_name
                if partner_id:
                    project_vals["partner_id"]=partner_id
                if pricelist_id:
                    project_vals["pricelist_id"]=pricelist_id

                #check if there is already an project to link
                proj_obj = self.pool.get("project.project")
                proj_id = None                
                
                # search project to order
                if order_id:
                    # if analytic id exist, search project with account
                    if analytic_id:
                        proj_id = proj_obj.search_id(cr, uid, [("analytic_account_id.order_id","=",order_id),("analytic_account_id","=",analytic_id)])
                    # otherwise search without account
                    else:
                        proj_id = proj_obj.search_id(cr, uid, [("analytic_account_id.order_id","=",order_id)])
                        analytic_id = get_fkey(proj_obj.read(cr, uid, proj_id, ["analytic_account_id"], context), "analytic_account_id")
                        
                # template
                template_id = shop.project_template_id and shop.project_template_id.id or None

                #create new or recreate from template if template has changed, only if analytic account created for this order
                if not analytic_id:
                    # create new or copy from template
                    project_vals["user_id"] = uid
                    if shop.project_template_id:
                        proj_id = proj_obj.copy(cr, uid, template_id, project_vals, project_context)
                    else:
                        proj_id = proj_obj.create(cr, uid, project_vals, project_context)
                    
                    # get analytic account
                    analytic_id = get_fkey(proj_obj.read(cr, uid, proj_id, ["analytic_account_id"], context), "analytic_account_id")
                    vals["project_id"] = analytic_id
                    return analytic_id
                
                # update current, if there exist a project to order
                elif proj_id:
                    
                    # get order                
                    order = None
                    order_project_template_id = None
                    if order_id:
                        order = self.browse(cr, uid, order_id, context=context)
                        order_project_template_id = order.shop_id.project_template_id and order.shop_id.project_template_id.id 
                    
                    # get project
                    proj = proj_obj.browse(cr, uid, proj_id, context=context)
                    
                    # proj update should be done?
                    proj_update = order and order.state == "draft" and proj_id and template_id and order_project_template_id != template_id
                    
                    # check if data from project vals are to update                    
                    if proj_update:
                        project_tmp_vals = proj_obj.copy_data(cr, uid, template_id, context=project_context)
                        project_tmp_vals.update(project_vals)
                        project_vals = project_tmp_vals
                    
                    proj_obj.write(cr, uid, [proj_id], project_vals, project_context)
                    vals["project_id"]=analytic_id
                    
                    # update all tasks
#                     if proj_update:
#                         proj = proj_obj.browse(cr, uid, proj_id, context=context)
#                         task_obj = self.pool["project.task"]
#                         cr.execute("SELECT t.id FROM project_task t WHERE t.project_id = %s", (proj_id,))
#                         task_ids = [r[0] for r in cr.fetchall()]
#                         if task_ids:
#                             for task_id in task_ids:
#                                 task_onchange_res = task_obj.onchange_project(cr, SUPERUSER_ID, task_id, proj_id, context=context)
#                                 task_values = task_onchange_res and task_onchange_res["value"] or {}
#                                 task_values["project_id"] = proj_id
#                                 task_obj.write(cr, SUPERUSER_ID, [task_id], task_values, context=context)
                                
        return False

    def _is_correct_analytic_field(self,cr,uid,vals,context=None):
        return vals.has_key("name") \
            or vals.has_key("partner_id") \
            or vals.has_key("pricelist_id") \
            or vals.has_key("shop_id") \
            or vals.has_key("client_order_ref")

    def write(self,cr,uid,ids,vals,context=None):
        if not context:
            context = {}
        if self._is_correct_analytic_field(cr, uid, vals, context):
            ids = util.idList(ids)
            for oid in ids:
                corrected_vals = vals.copy()
                self._correct_analytic_values(cr,uid,oid,corrected_vals,context)
                super(sale_order,self).write(cr,uid,oid,corrected_vals,context)
            return True
        res = super(sale_order,self).write(cr,uid,ids,vals,context)
        return res

    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}

        if vals.get("name", "/") == "/":
            vals["name"] = self.pool.get("ir.sequence").get(cr, uid, "sale.order") or "/"

        analytic_account_id = self._correct_analytic_values(cr,uid,None,vals,context)
        order_id = super(sale_order,self).create(cr, uid, vals, context)

        #check if a new analytic account is created
        #if it is, link it with order
        if order_id and analytic_account_id:
            analytic_account_obj = self.pool.get("account.analytic.account")
            analytic_account_obj.write(cr, uid, [analytic_account_id], { "order_id" : order_id }, context=context)
        return order_id

    def _pre_calc(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            total = obj.margin
            total -= obj.timesheet_lines_amount
            res[obj.id]=total
        return res

    def _post_calc(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id]= obj.project_id and obj.project_id.balance or 0.0
        return res

    def _timesheet_lines(self,cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for oid in ids:
            res[oid]=[]

        cr.execute(
         " SELECT o.id,tl.id FROM hr_analytic_timesheet AS tl "
         "   INNER JOIN account_analytic_line AS l ON l.id = tl.line_id "
         "   INNER JOIN account_analytic_account AS a ON a.id = l.account_id "
         "   INNER JOIN sale_order AS o ON o.project_id = a.id AND o.name = a.name "
         "   WHERE o.id IN %s"
         "   ORDER BY 1 ",
         (tuple(ids),)
        )

        for row in cr.fetchall():
            res[row[0]].append(row[1])
        return res

    def _timesheet_lines_amount(self,cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids,0.0)

        cr.execute(
        "SELECT o.id,SUM(l.amount) FROM hr_analytic_timesheet AS tl "
        "     INNER JOIN account_analytic_line AS l ON l.id = tl.line_id "
        "     INNER JOIN account_analytic_account AS a ON a.id = l.account_id "
        "     INNER JOIN sale_order AS o ON o.project_id = a.id AND o.name = a.name "
        "     WHERE o.id IN %s"
        "     GROUP BY 1 ",
         (tuple(ids),)
        )

        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res

    def _contrib_margin_percent(self,cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            margin = 0.0
            if obj.amount_untaxed:
                margin=100.0/obj.amount_untaxed*obj.margin
            res[obj.id]=margin
        return res
    
    def _linked_project_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        project_obj = self.pool["project.project"]
        project_ids = project_obj.search(cr, uid, [("order_id","in",ids)])
        for project in project_obj.browse(cr, uid, project_ids, context=context):
            res[project.order_id.id] = project.id
        return res

    _inherit = "sale.order"
    _columns = {
        "pre_calc" : fields.function(_pre_calc,string="Pre Calculation (Netto)",type="float", digits_compute=dp.get_precision("Account")),
        "post_calc" : fields.function(_post_calc,string="Post Calculation (Netto)",type="float", digits_compute=dp.get_precision("Account")),
        "margin_contrib_percent" : fields.function(_contrib_margin_percent,string="Contribution Margin %",type="float"),
        "timesheet_lines" : fields.function(_timesheet_lines,string="Timesheet Lines",type="many2many",obj="hr.analytic.timesheet"),
        "timesheet_lines_amount" : fields.function(_timesheet_lines_amount,string="Timesheet Lines",type='float', digits_compute=dp.get_precision("Account")),
        "order_project_id" : fields.function(_linked_project_id, relation="project.project", type="many2one", string="Project")
     }
    
    
class sale_order_line(osv.osv):
  
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id, context)
                
        product = line.product_id
        if product and product.type == "service" and product.billed_at_cost:
            task_obj = self.pool["project.task"]
            task_ids = task_obj.search(cr, SUPERUSER_ID, [("sale_line_id","=",line.id)])
            f = format.LangFormat(cr, uid, context=context)
            
            task_set = set()  
            work_info = []        
            effective_hours = 0.0
            
            # add task and childs
            def add_task(task):
                # check if task already processed
                if task.id in task_set:
                    return 0.0
                
                hours = 0.0
                
                # check work 
                for work in task.work_ids:
                    if work.hours:
                        hours+=work.hours
                        work_line = []
                        
                        # append date
                        if work.date:
                            work_line.append(f.formatLang(util.timeToDateStr(work.date), date=True))
                       
                        # append time
                        work_line.append(_("%s Hour(s)") % f.formatLang(work.hours, float_time=True))
                             
                        # append name
                        if work.name:
                            work_line.append(work.name)
                            
                        work_info.append(" - ".join(work_line))
        
                # add childs
                task_set.add(task.id)
                for child_task in task.child_ids:
                    hours += add_task(child_task)
                
                return hours
                    
            
            # build task set
            for task in task_obj.browse(cr, SUPERUSER_ID, task_ids, context=context):
                effective_hours += add_task(task)
                
            # get quantity
            res["quantity"] = max(effective_hours, res["quantity"])
            # set new work info
            if work_info:
                res["name"] = "%s\n%s" % (res["name"], "\n".join(work_info))
            
        return res
    
    
    _inherit = "sale.order.line"
