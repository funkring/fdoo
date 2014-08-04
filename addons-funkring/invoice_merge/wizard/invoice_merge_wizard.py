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
from openerp.tools.translate import _
from openerp.addons.at_base import util
from openerp.addons.at_base import helper

class invoice_merge_wizard(osv.osv_memory):
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(invoice_merge_wizard,self).default_get(cr,uid,fields_list,context)
        if not context or context.get("active_model") != "account.invoice":    
            return res
        
        invoice_ids = context.get("active_ids") or []
        invoice_obj = self.pool.get("account.invoice")        
        invoice_merge = {}
                        
        for invoice in invoice_obj.browse(cr,uid,invoice_ids,context):
            invoice_key = (invoice.partner_id,invoice.type)
            data = invoice_merge.get(invoice_key)
            if not data:                
                data = {       
                    "name" : _("Collective Invoice"),             
                    "partner_id" : invoice.partner_id.id,
                    "type" : invoice.type,
                    "info" : [],
                    "invoice_ids" : [],
                    "comment" : [],
                    "payment_term" :  invoice.payment_term and invoice.payment_term.id or None,
                    "fiscal_position" : invoice.fiscal_position and invoice.fiscal_position.id or None,                    
                    "company_id" : invoice.company_id.id,
                    "account_id" : invoice.account_id.id,
                    "journal_id" : invoice.journal_id.id,
                    "currency_id": invoice.currency_id.id,
                    "user_id" : uid,
                }
                invoice_merge[invoice_key]=data
                        
            data_state = data.get("state") or 0
            data_num = data.get("num_of_invoices") or 0
            data_amount = data.get("amount") or 0.0
            data_info = data["info"]
            data_invoice_ids = data["invoice_ids"]
            data_comment = data["comment"]
            dt_invoice = invoice.date_invoice and util.strToDate(invoice.date_invoice) or None
            dt_from_date = data.get("from_date") or None
            dt_to_date = data.get("to_date") or None
                                                
            def addInfo(infoState, infoText):
                data_info.append(infoText)
                return max(data_state,infoState)
                                    
            if invoice.state == "draft":
                data_invoice_ids.append(invoice.id)
                data_amount += invoice.amount_total
                
                if invoice.comment:
                    data_comment.append(invoice.comment)
                                
                if dt_invoice:
                    dt_from_date = (dt_from_date and min(dt_from_date,dt_invoice)) or dt_invoice                    
                    dt_to_date = (dt_to_date and max(dt_to_date,dt_invoice)) or dt_invoice
                    
                data_num += 1
            else:
                data_state=addInfo(1,_("%s is no draft Invoice, Ignored!") % (invoice.name,)) 
            
            data["amount"]=data_amount
            data["state"]=data_state
            data["num_of_invoices"]=data_num
            data["from_date"]=dt_from_date
            data["to_date"]=dt_to_date
                               
        
        def mergeLines(key):
            textLines = data[key]
            if not textLines:
                del data[key]
            else:
                data[key]="\n".join(textLines)
        
        def toStrDate(key):
            dtValue = data[key]
            if dtValue:
                dtValue=util.dateToStr(dtValue)
                data[key]=dtValue
            return dtValue
        
        
        res_merge_ids=[]
        for data in invoice_merge.values():
            mergeLines("info")
            mergeLines("comment")
            str_range = helper.getMonthYearRange(cr, uid,  toStrDate("from_date"), toStrDate("to_date"), context)
            if str_range:            
                data["name"] = _("Collective Invoice %s") % (str_range,)
            data["invoice_ids"]=[(6,0,data["invoice_ids"])]
            res_merge_ids.append(data)            
           
        res["merge_ids"]=res_merge_ids
        return res
    
                    
    def do_merge(self, cr, uid, ids, context=None):        
        invoice_obj = self.pool.get("account.invoice")
        invoice_line_obj = self.pool.get("account.invoice.line")
        wkf_workitem_obj = self.pool.get("workflow.workitem")
        picking_obj = self.pool.get("stock.picking")
        purchase_obj = self.pool.get("purchase.order")        
        sale_obj = self.pool.get("sale.order")
                
        #check if account analytic_line invoice_id exists
        account_analytic_line_obj = self.pool.get("account.analytic.line")        
        has_analytic_invoice = (account_analytic_line_obj and account_analytic_line_obj.fields_get(cr,uid,"invoice_id") and True) or False 
                
        for wizard in self.browse(cr, uid, ids, context):
            for merge in wizard.merge_ids:
                # if only one or none invoice do continue
                if merge.num_of_invoices <= 1:
                    continue
                
                invoice_ids = []
                values =  {             
                    "name" : merge.name,       
                    "type" : merge.type,
                    "account_id" : merge.account_id.id,
                    "partner_id" : merge.partner_id.id,
                    "journal_id" : merge.journal_id.id,
                    "currency_id" : merge.currency_id and merge.currency_id.id or None,
                    "comment" : merge.comment,
                    "payment_term" : merge.payment_term and  merge.payment_term.id or None,
                    "fiscal_position" : merge.fiscal_position and merge.fiscal_position.id or None,
                    "date_invoice" : merge.date,
                    "company_id" : merge.company_id.id,
                    "user_id" : merge.user_id.id                  
                }   
                invoice_id = invoice_obj.create(cr,uid,values,context=context)
                                
                for invoice in merge.invoice_ids:
                    invoice_ids.append(invoice.id)                        
                    for line in invoice.invoice_line:
                        origin = line.origin                                                                     
                        if invoice.origin and (not origin or invoice.origin not in origin):
                            origin = origin and ":".join((invoice.origin,origin)) or invoice.origin or None
                             
                        invoice_line_obj.write(cr,uid,line.id, {
                            "origin" : origin,
                            "invoice_id" : invoice_id
                        },context=context)                        
                
                #correct work flows
                cr.execute("SELECT id FROM wkf_instance WHERE res_type='account.invoice' AND res_id=%s",(invoice_id,))
                new_wkf_inst_id=None
                for row in cr.fetchall():
                    new_wkf_inst_id = row[0]
                
                #get subworkflows of existing invoices
                work_item_ids=[]
                if new_wkf_inst_id:
                    cr.execute("SELECT item.id FROM wkf_workitem AS item "
                               " INNER JOIN wkf_instance AS subinst ON subinst.id=item.subflow_id "
                               "            AND subinst.res_type='account.invoice' " 
                               "            AND subinst.res_id IN %s", (tuple(invoice_ids),))
                    for row in cr.fetchall():
                        work_item_ids.append(row[0])
                
                #update work items   
                if work_item_ids:
                    wkf_workitem_obj.write(cr,uid,work_item_ids, {"subflow_id" : new_wkf_inst_id})
                                          
                #update relations
                if invoice_ids:
                    def getInvDepIds(relTable,relCol):                        
                        sqlStmt = "SELECT " + relCol + " FROM " + relTable + " WHERE invoice_id IN %s"
                        cr.execute(sqlStmt,(tuple(invoice_ids),))
                        res = [r[0] for r in cr.fetchall()]                            
                        return res
                    
                    # Not more used 
                    #depIds = getInvDepIds("picking_invoice_rel","picking_id")
                    #picking_obj.write(cr,uid,depIds,{"invoice_ids" : [(4,invoice_id)] },context)
                    
                    depIds = getInvDepIds("purchase_invoice_rel","purchase_id")                   
                    purchase_obj.write(cr,uid,depIds,{"invoice_ids" : [(4,invoice_id)] },context)
                                        
                    depIds = getInvDepIds("sale_order_invoice_rel","order_id")
                    sale_obj.write(cr,uid,depIds,{"invoice_ids" : [(4,invoice_id)] },context)
                    
                    if has_analytic_invoice:
                        depIds = getInvDepIds("account_analytic_line","id")
                        account_analytic_line_obj.write(cr,uid,depIds,{"invoice_id" : invoice_id},context)
                        
                    invoice_obj._replace_invoice_ids_with_id(cr, uid, invoice_ids, invoice_id, context)
                                        
                #remove other invoices
                invoice_obj.unlink(cr, uid, invoice_ids, context)
                #compute new invoice
                invoice_obj.button_compute(cr, uid, [invoice_id], {"type": merge.type }, set_total=True)                
                
        return { "type" : "ir.actions.act_window_close" }
                
    
    _name = "invoice_merge.wizard"
    _description="Invoice Merge Wizard"
    _columns = {        
        "merge_ids" : fields.one2many("invoice_merge.merge","wizard_id","Invoices"),
    }


class invoice_merge(osv.osv_memory):        
    _name="invoice_merge.merge"    
    _description="Invoice Merge"
    _columns = {
        "wizard_id" : fields.many2one("invoice_merge.wizard","Wizard"),
        "date" : fields.date("Date"),
        "from_date" : fields.date("From Date"),
        "to_date" : fields.date("To Date"),
        "name": fields.char("Description", size=64),
        "partner_id" : fields.many2one("res.partner","Partner"),
        "num_of_invoices" : fields.integer("Num. of Invoices"),
        "amount" : fields.float("Amount",readonly=True),
        "state" : fields.selection([(0,"Ok"),(1,"Warning"),(2,"Error")],"State",readonly=True,type="integer"),
        "info" : fields.text("Info"),
        "invoice_ids" : fields.many2many("account.invoice","invoice_merge_invoice_rel","wizard_id","merge_id","Invoices"),
        "journal_id": fields.many2one("account.journal", "Journal", required=True),
        "type": fields.selection([
            ("out_invoice","Customer Invoice"),
            ("in_invoice","Supplier Invoice"),
            ("out_refund","Customer Refund"),
            ("in_refund","Supplier Refund"),
            ],"Type"),
        "comment" : fields.text("Comment"),
        "payment_term": fields.many2one("account.payment.term", "Payment Term"),
        "fiscal_position": fields.many2one("account.fiscal.position", "Fiscal Position"),
        "company_id": fields.many2one("res.company", "Company"),
        "user_id": fields.many2one("res.users", "Salesman"),
        "account_id": fields.many2one("account.account", "Account"),
        "currency_id": fields.many2one("res.currency", "Currency", required=True),
    }

