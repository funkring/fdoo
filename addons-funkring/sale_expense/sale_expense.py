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


from openerp.osv import fields,osv
import decimal_precision as dp
from at_base import util
from openerp.tools.translate import _


class sale_order(osv.osv):

    def copy_data(self, cr, uid, oid, default=None, context=None):

        if not default:
            default = {}
        if not default.has_key("expense_status"):
            default["expense_status"]="draft"
        
        copy_id = super(sale_order, self).copy_data(cr, uid, oid, default, context)
        
        return copy_id

    def do_expense_validate(self, cr, uid, ids, context=None):

        self.write(cr,uid,ids,{"expense_status" : "valid"})
        self.create_invoice(cr, uid, ids)
        self.create_timesheet(cr, uid, ids)
        
        return True

    def create_invoice(self, cr, uid, ids, context=None):
        
        expense_purchase_obj = self.pool.get("sale_expense.expense_purchase_lines")
        invoice_line_obj = self.pool.get("account.invoice.line")
        invoice_obj = self.pool.get("account.invoice")
       
        for order in self.browse(cr, uid, ids):
            for exp_line in order.expense_purchase_lines_ids :
                invoice_id = None 
                vals =  {                
                   "name" : exp_line.name,
                   "price_unit" : exp_line.price,
                   "quantity" : exp_line.quantity,
                   "account_id" : exp_line.account_id.id,
                   "account_analytic_id" : order.project_id.id,
                   "product_id" : exp_line.product_id.id
                }
                if not exp_line.invoice_line_id:
                    invoice_id = invoice_obj.create(cr, uid, {"reference_type" : "none",
                                     "reference" : order.name,
                                     "name" : order.name,
                                     "partner_id" : exp_line.supplier_id.id, 
                                     "address_invoice_id" : order.partner_invoice_id.id, 
                                     "account_id" : order.partner_id.property_account_payable.id, 
                                     "currency_id" : order.pricelist_id.currency_id.id,
                                     "journal_id" : exp_line.journal_id.id,
                                     "company_id" : order.company_id.id,
                                     "type" : "in_invoice"
                                     }, context)
                    vals["invoice_id"]=invoice_id
                    invoice_line_id = invoice_line_obj.create(cr, uid, vals, context)
                    expense_purchase_obj.write(cr, uid, exp_line.id, {"invoice_line_id" : invoice_line_id})
                else:                   
                    invoice_line_obj.write(cr, uid, exp_line.id, vals, context)
               
        return True
    
    
    def create_timesheet(self, cr, uid, ids, context=None):
        
        expense_employee_obj = self.pool.get("sale_expense.expense_employee_lines")
        timesheet_line_obj = self.pool.get("hr.analytic.timesheet")
        timesheet_obj = self.pool.get("hr_timesheet_sheet.sheet")
        analytic_line_obj = self.pool.get("account.analytic.line")
        account_id = None
        amount = 0.00
        product_uom_id = None
        for order in self.browse(cr, uid, ids):
            for exp_line in order.expense_employee_lines_ids:
                product_id = exp_line.employee_id.product_id
                res = analytic_line_obj.on_change_unit_amount(cr, exp_line.employee_id.user_id.id, 0, product_id.id, 
                                                 exp_line.unit_amount, exp_line.employee_id.user_id.company_id.id, False, False, context)
                
                
                journal_id = timesheet_line_obj._getAnalyticJournal(cr, uid, context)
                if not journal_id:
                    journal_ids = self.pool.get('account.analytic.journal').search(cr, uid, [('type','=','purchase')])
                    journal_id = journal_ids and journal_ids[0] or False
                try:
                    account_id = res["value"]["general_account_id"]
                    amount = res["value"]["amount"]
                    product_uom_id = res["value"]["product_uom_id"]
                except Exception,e:
                    raise osv.except_osv(_('Error'), _('There is no product defined for the employee. You have to insert a product for the employee if you want to continue!'))
                vals = {
                    "name" : exp_line.name,
                    "date" : exp_line.date,
                    "unit_amount" : exp_line.unit_amount,
                    "user_id" : exp_line.employee_id.user_id.id,
                    "amount" : amount,
                    "account_id" : order.project_id.id,
                    "journal_id" : journal_id,
                    "general_account_id" : account_id,
                    "product_uom_id" : product_uom_id
                }
                timesheet = timesheet_obj.search(cr, uid, [("date_from", "=", util.getFirstOfMonth(exp_line.date)), ("employee_id", "=", exp_line.employee_id.id)])
                if timesheet:
                    if exp_line.timesheet_line_id:
                        timesheet_line_obj.write(cr, uid, exp_line.timesheet_line_id.id, vals)
                        continue
                else:
                    timesheet_obj.create(cr, uid, {
                                              "employee_id" : exp_line.employee_id.id,
                                              "user_id" : exp_line.employee_id.user_id.id,
                                              "date_from" : util.getFirstOfMonth(exp_line.date),
                                              "date_to" : util.getEndOfMonth(exp_line.date),
                                              "date_current" : exp_line.date,
                                              "state" : "new",}, context)
                timesheet_line_id = timesheet_line_obj.create(cr, uid, vals, context)
                expense_employee_obj.write(cr, uid, exp_line.id, {"timesheet_line_id" : timesheet_line_id})
                
        return True

    def do_expense_draft(self, cr, uid, ids, context=None):

        self.write(cr,uid,ids,{"expense_status" : "draft"})
        
        return True
    
    def expense_init(self,cr,uid,ids,context=None):
        
        expense_purchase_obj = self.pool.get("sale_expense.expense_purchase_lines")
        for item in self.browse(cr, uid, ids):
            expense_purchase_lines = item.expense_purchase_lines_ids
            for line in expense_purchase_lines:
                if line.date < item.date_order:
                    expense_purchase_obj.write(cr,uid,line.id,{"date" : item.date_order})
    
    def action_wait(self, cr, uid, ids, *args):    
               
        res = super(sale_order,self).action_wait(cr,uid,ids,args)
        self.expense_init(cr, uid, ids)
        
        return res
    

    _inherit="sale.order"
    _columns = {
        "expense_status" : fields.selection([("draft", "Draft"), ("valid", "Validated")], "Status"),
        "expense_purchase_lines_ids" : fields.one2many("sale_expense.expense_purchase_lines", "sale_order_id", "Expense Purchase Lines"),
        "expense_employee_lines_ids" : fields.one2many("sale_expense.expense_employee_lines", "sale_order_id", "Expense Employee Lines"),       
    }
    _defaults = { 
        "expense_status" : "draft"
    }

sale_order()


class expense_purchase_lines(osv.osv):
    
    def copy_data(self, cr, uid, oid, default=None, context=None):
        
        if not default:
            default = {}
        if not default.has_key("invoice_line_id"):
            default["invoice_line_id"]=None
        
        copy_id = super(expense_purchase_lines, self).copy_data(cr, uid, oid, default, context)
        
        return copy_id    
    
    def on_change_product(self, cr, uid, ids, product_id, fposition_id=False, context=None):
        
        res_value = {}
        res = {
            "value" : res_value
        }
        if product_id:
            product = self.pool.get("product.product").browse(cr, uid, product_id)
            res_value["account_id"] = product.product_tmpl_id.categ_id.property_account_expense_categ.id
            res_value["price"] = product.lst_price
            res_value["name"] = product.name_template + " - " + product.variants
        return res

    def _is_invoiced(self, cr, uid, ids, field_name, arg, context=None):        
        
        res = dict.fromkeys(ids)        
        for obj in self.browse(cr, uid, ids):
            invoice_line = obj.invoice_line_id
            invoice = invoice_line and invoice_line.invoice_id or None
            res[obj.id]=invoice and invoice.state=="open" or False        
            
        return res
    
    def _amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        tax_obj = self.pool.get('account.tax')
        for obj in self.browse(cr, uid, ids):
            product = obj.product_id
            price = obj.price
            quantity = obj.quantity
            taxes = tax_obj.compute_all(cr, uid, product.taxes_id, price, quantity, product=product.id)
            res[obj.id] = taxes["total"]
                
        return res
            
    
    _name="sale_expense.expense_purchase_lines"
    _columns = {
        "name" : fields.char("Description",128, required=True),
        "sale_order_id" : fields.many2one("sale.order", "Sale Order",select=True),
        "date" : fields.date("Date", required=True),
        "supplier_id" : fields.many2one("res.partner", "Supplier", required=True),
        "journal_id" : fields.many2one("account.journal", "Journal", required=True, domain=[("type","=","purchase")]),
        "product_id" : fields.many2one("product.product", "Product", required=True),
        "quantity" : fields.float("Quantity"),
        "price" : fields.float("Price", digits_compute= dp.get_precision('Account')),
        "amount_total" : fields.function(_amount_total, type="float", string="Total", digits_compute= dp.get_precision('Account')),    
        "invoice_line_id" : fields.many2one("account.invoice.line", "Invoice Line", ondelete="set null"),
        "is_invoiced" : fields.function(_is_invoiced, type="boolean", readonly=True, string="Invoiced"),
        "account_id": fields.many2one("account.account", "Account", required=True, domain=[("type","<>","view"), ("type", "<>", "closed")], help="The income or expense account related to the selected product."),
    }
    
    _defaults = {
        "quantity" : 1.00
    }
    
expense_purchase_lines()


class expense_employee_lines(osv.osv):
    
    def copy_data(self, cr, uid, oid, default=None, context=None):
        
        if not default:
            default = {}
        if not default.has_key("timesheet_line_id"):
            default["timesheet_line_id"]=None
        
        copy_id = super(expense_employee_lines, self).copy_data(cr, uid, oid, default, context)
        
        return copy_id
    
    def _is_open(self, cr, uid, ids, field_name, arg, context=None):
        
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids):
            timesheet_id = self.get_timesheet(cr, uid, ids, obj.date)         
            timesheet = self.pool.get("hr_timesheet_sheet.sheet").browse(cr, uid, timesheet_id) 
            if timesheet.state == "draft" or timesheet.state == "new":
                res[obj.id]=True
                
        return res
    
    def get_timesheet(self,cr,uid,ids,str_date,context=None):
        
        timesheet = self.pool.get("hr_timesheet_sheet.sheet")
        if context is None:
            context = {}     
        for obj in self.browse(cr, uid, ids):
            timesheet_ids = timesheet.search(cr, uid, [("employee_id","=",obj.employee_id.id),("date_from","<=",str_date), ("date_to",">=",str_date)], context=context)
            if timesheet_ids:
                return timesheet_ids[0]
        return None
    
    def on_change_employee(self, cr, uid, ids, date, context=None):
        
        res_value = {}
        res = {
            "value" : res_value
        }
        for obj in self.browse(cr, uid, ids):    
            if not date:
                res_value["date"] =  obj.sale_order_id.date_order
                
        return res
    
    
    _name="sale_expense.expense_employee_lines"
    _columns = {
        "sale_order_id" : fields.many2one("sale.order", "Sale Order",select=True),
        "employee_id": fields.many2one("hr.employee", "Employee", required=True),
        "name" : fields.char("Description", size=128, required=True),
        "date" : fields.date("Date", required=True),
        "unit_amount" : fields.float("Quantity", required=True),
        "timesheet_line_id" : fields.many2one("hr.analytic.timesheet", "Timesheet Line"),
        "is_open" : fields.function(_is_open, type="boolean", string="Open"),
    }
expense_employee_lines()                                                                                                                                        