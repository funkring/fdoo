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
import openerp.addons.decimal_precision as dp

class sale_shop(osv.osv):
    _inherit = "sale.shop"
    _columns = {
        "autocreate_order_parent_id": fields.many2one('account.analytic.account', 'Analytic account default parent'),
        "autocreate_order_analytic_account" : fields.boolean("Analytic Account per Order")
    }

class sale_order(osv.osv):

    def _project_name_get(self,cr,uid,order_values):
        order_name = order_values.get("name","")
        client_order_ref = order_values.get("client_order_ref")
        if client_order_ref:
            return "%s / %s" % (order_name,client_order_ref)
        return order_name


        #get foreign key value
    def _correct_analytic_values(self,cr,uid,order_id,vals,context=None):
        """ Sync analytic account and sale order

            :returns: analytic account id if a new one is created otherwise False is returned
        """
        def get_fkey(inDict,inKey):
            res = inDict.get(inKey,None)
            if res:
                return res[0]
            return None

        project_id = None
        order_values = {}

        if order_id:
            order_read = self.read(cr, uid, order_id, ["project_id","partner_id","pricelist_id","name","shop_id"], context)
            order_values["project_id"]=get_fkey(order_read,"project_id")
            order_values["partner_id"]=get_fkey(order_read,"partner_id")
            order_values["pricelist_id"]=get_fkey(order_read,"pricelist_id")
            order_values["client_order_ref"]=order_read.get("client_order_ref")
            order_values["name"]=order_read.get("name")
            order_values["shop_id"]=get_fkey(order_read,"shop_id")
            project_id = order_values.get("project_id")
        else:
            if not vals.get("name"):
                vals["name"]=self.default_get(cr, uid, ["name"], context)["name"]

        shop_id = vals.get("shop_id",order_values.get("shop_id",context.get("shop")))
        if shop_id:
            shop=self.pool.get("sale.shop").browse(cr, uid, shop_id,context=context)
            if shop.autocreate_order_analytic_account:
                partner_id=order_values["partner_id"]=vals.get("partner_id",order_values.get("partner_id"))
                pricelist_id=order_values["pricelist_id"]=vals.get("pricelist_id",order_values.get("pricelist_id"))
                order_values["name"]=vals.get("name",order_values.get("name"))
                order_values["client_order_ref"]=vals.get("client_order_ref",order_values.get("client_order_ref"))

                project_obj = self.pool.get("account.analytic.account")
                project_context=context.copy()
                project_vals = {}

                project_name = self._project_name_get(cr,uid,order_values)
                partner_id = order_values.get("partner_id")

                #init new
                project_order_id = None
                if not project_id:
                    project_context['partner_id']=partner_id
                    project_context['pricelist_id']=pricelist_id
                    project_context['default_name']=project_name
                #init update
                else:
                    project_order_id = get_fkey(project_obj.read(cr,uid,project_id,["order_id"]),"order_id")
                    project_vals["name"]=project_name
                    if partner_id:
                        project_vals["partner_id"]=partner_id
                    if pricelist_id:
                        project_vals["pricelist_id"]=pricelist_id

                #init all and determine parent project
                shop_project_id = shop.autocreate_order_parent_id.id
                parent_project = None

                # get parent project
                parent_project_id = context.get("parent_project_id",None)
                if parent_project_id:
                    parent_project = project_obj.browse(cr,uid,parent_project_id,context=context)
                elif project_id:
                    project = project_obj.browse(cr,uid,project_id,context=context)
                    parent_project = project.parent_id

                # check if parent is valid
                if parent_project:
                    # reset project parent if it has not an order id
                    if not parent_project.order_id:
                        parent_project = None
                    else:
                        #reset parent_project if parent_project shop is not the same
                        #as the shop now
                        shop_obj = self.pool.get("sale.shop")
                        parent_shop_id = shop_obj.search_id(cr,uid,[("autocreate_order_parent_id","=",parent_project.id)])
                        if parent_shop_id and parent_shop_id != shop_id:
                            parent_shop_id=None

                # check for partner project
                if partner_id:
                    partner = self.pool.get("res.partner").browse(cr,uid,partner_id)
                    partner_account = partner.property_partner_analytic_account
                    if partner_account:
                        parent_project = partner_account

                # set values
                project_vals["parent_id"] = (parent_project and parent_project.id) or shop_project_id
                project_vals["code"]= order_values.get("name")
                project_vals["order_id"]=order_id

                #check if there is already an project to link
                proj_obj = self.pool.get("project.project")
                # search order id
                if order_id and not project_id:
                    project_id = proj_obj.search_id(cr, uid, [("analytic_account_id.order_id","=",order_id)])
                    project_order_id = order_id

                #create new
                if not project_id:
                    proj_id = proj_obj.create(cr,uid,project_vals,project_context)
                    project_id = get_fkey(proj_obj.read(cr, uid, proj_id, ["analytic_account_id"], context),"analytic_account_id")
                    vals["project_id"]=project_id
                    return project_id
                #update current, if it is the
                # analytic account created for this order
                elif project_order_id == order_id:
                    project_obj.write(cr, uid, [project_id], project_vals,project_context)
                    vals["project_id"]=project_id
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
        res = {}
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
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            margin = 0.0
            if obj.amount_untaxed:
                margin=100.0/obj.amount_untaxed*obj.margin
            res[obj.id]=margin
        return res

    _inherit = "sale.order"
    _columns = {
        "pre_calc" : fields.function(_pre_calc,string="Pre Calculation (Netto)",type="float", digits_compute=dp.get_precision("Account")),
        "post_calc" : fields.function(_post_calc,string="Post Calculation (Netto)",type="float", digits_compute=dp.get_precision("Account")),
        "margin_contrib_percent" : fields.function(_contrib_margin_percent,string="Contribution Margin %",type="float"),
        "timesheet_lines" : fields.function(_timesheet_lines,string="Timesheet Lines",type="many2many",obj="hr.analytic.timesheet"),
        "timesheet_lines_amount" : fields.function(_timesheet_lines_amount,string="Timesheet Lines",type='float', digits_compute=dp.get_precision("Account"))
     }
