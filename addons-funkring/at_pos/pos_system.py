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
from openerp.tools.translate import _
from at_base import format
from at_base import util
from at_base import helper
from escpos import Escpos
import tcm

class pos_printer(osv.osv):
    
    def _get_printer(self,cr,uid,printer_id,context=None):
        if not printer_id:
            printer_id = self.search_id(cr, uid, [], context=context)
        if not printer_id:
            raise osv.except_osv(_("Error"), _("There is no POS Printer defined!"))
        return self.browse(cr, uid, printer_id, context)       
    
    _columns = {
        "name" : fields.char("Name",size=64,required=True,select=True),
        "type" : fields.selection([("local","Local"),("esc_net","ESC/POS Network Printer")],"Type",required=True,select=True)
    }
    _name="at_pos.pos_printer"
    _description="POS Printer"
    
pos_printer()


class pos_system(osv.osv):
    
    def _tc_statement_status_get(self,cr,uid,statement,context=None):
        return tcm.tcm_status(statement, {
                                    "draft" : (tcm.NO_PRIORITY,_("Opening")),
                                    "open" : (tcm.NO_PRIORITY,_("Balancing")),
                                    "confirm" : (tcm.HIGHEST_PRIORITY,_("Closed"))
                                })
        
    def _tc_order_status_get(self,cr,uid,order,context=None): 
        return tcm.tcm_status(order, { 
                                "draft" : (tcm.NO_PRIORITY, _("Sale")),
                                "payment" : (tcm.NO_PRIORITY, _("Payment")),
                                "advance" : (tcm.NO_PRIORITY, _("Advance")),
                                "paid" : (tcm.NO_PRIORITY, _("Paid")),
                                "done" : (tcm.NO_PRIORITY, _("Done")),
                                "cancel" : (tcm.NO_PRIORITY,_("Cancel"))
                            })
    def _tc_system_get(self,cr,uid,oid,context=None):
        system = self.browse(cr, uid, oid, context)
        if not system:
            raise osv.except_osv(_("Error"), _("POS System with ID %s is invalid!") % (oid,))
        return system
        
    def _tc_journals(self,cr,uid,system,context=None):
        res = [system.cash_journal_id]
        if system.balance_journal_id:
            res.append(system.balance_journal_id)
        if system.voucher_journal_id:
            res.append(system.voucher_journal_id)
        return res

    def _tc_journal_ids(self,cr,uid,system,context=None):
        return [j.id for j in self._tc_journals(cr, uid, system, context)]
        
    def _tc_partner_get(self,cr,uid,partner,context=None):
        res = tcm.tcm_name(partner)
        res["balance"] = partner.calculated_balance
        return res
    
    def _tc_payment_get(self,cr,uid,payment,context=None):                
        res = tcm.tcm_name(payment)
        res["type"]=payment.type
        res["amount"]=payment.amount
        return res
    
    def _tc_product_code_profile_get(self,cr,uid,code_profile,context=None):
        res = tcm.tcm_name(code_profile)
        res["length"]=code_profile.length
        res["code_pos"]=code_profile.code_pos
        res["code_length"]=code_profile.code_length
        res["price_pos"]=code_profile.price_pos
        res["price_length"]=code_profile.price_length
        res["price_post_decimal_pos"]=code_profile.price_post_decimal_pos
        res["price_post_decimal_length"]=code_profile.price_post_decimal_length
        res["amount_pos"]=code_profile.amount_pos
        res["amount_length"]=code_profile.amount_length
        res["amount_post_decimal_pos"]=code_profile.amount_post_decimal_pos
        res["amount_post_decimal_length"]=code_profile.amount_post_decimal_length
        return res
    
    def _tc_cash_detail_get(self,cr,uid,detail):
        return {
            "id" : detail.id,
            "value" : detail.pieces,
            "amount" : detail.number,
            "subtotal" : detail.subtotal
        }
               
    def _tc_validate_payment(self, cr, uid, order_id, context=None):
        payment_obj = self.pool.get("pos.order.payment")        
        payment_ids  = payment_obj.search(cr,uid,[("order_id","=",order_id)])        
        res = []
        if payment_ids:
            order_obj = self.pool.get("pos.order")
            order = order_obj.browse(cr,uid,order_id,context=context)
            #
            total = order.amount_total
            other_payment = order.payment_other
            cash_payment = order.payment_cash
            cash_payment_should = (total - other_payment)
            #
            if cash_payment != cash_payment_should:                                
                cash_ids = payment_obj.search(cr,uid,[("order_id","=",order_id),("type","=","cash")])
                cash_id = cash_ids and cash_ids[0] or None                
                cash_values = {
                    "order_id" : order_id,
                    "type" : "cash",
                    "amount" : cash_payment_should }
                
                if not cash_id:
                    payment_obj.create(cr,uid,cash_values,context=context)
                else:
                    payment_obj.write(cr,uid,cash_id,cash_values,context=context)            
                               
            types = dict(payment_obj.fields_get(cr, uid,["type"],context)["type"]["selection"])
            for payment in payment_obj.browse(cr,uid,payment_ids,context=context):
                payment_res = tcm.tcm_name(payment)
                payment_res["type"]={ "name" : payment.type, "description" : types[payment.type] } 
                payment_res["amount"]=payment.amount
                if payment.balance:
                    payment_res["balance"]=payment.balance
                res.append(payment_res)
        return res
    
    def _tc_child_statement_get(self,cr,uid,oid,parent_statement,journal,context=None):                
        statement_obj = self.pool.get("account.bank.statement")
                        
        if parent_statement.journal_id.id == journal.id:
            raise osv.except_osv(_("Error"), _("Child cash statement could not have the same journal (%s) as the main cash statement (%s)") % 
                                               (journal.name,parent_statement.journal_id.name) )
        
        statement_ids = statement_obj.search(cr,uid,[("parent_id","=",parent_statement.id),("journal_id","=",journal.id),("state","!=","confirm")])
        statement_state = "draft"
        statement_id = None
        if statement_ids:
            statement_id = statement_ids[0]
            statement_state = statement_obj.read(cr,uid,statement_id,["state"],context=context)["state"]
        else:
            statement_id = statement_obj.create(cr,uid,{
                                            "parent_id" : parent_statement.id,
                                            "journal_id" : journal.id,
                                            "starting_details_ids" : [],
                                            "ending_details_ids" : []
                                        },context=context)
        
        if statement_state == "draft":
            statement_obj.button_open(cr,uid,[statement_id],context=context)
        return statement_id
    
    def _tc_cleanup(self, cr, uid, oid, statement_id, context=None):
        order_obj = self.pool.get("pos.order")
        order_ids = order_obj.search(cr,uid,[("statement_id","=",statement_id),("state","=","draft")])   
        order_obj.unlink(cr,uid,order_ids,context=context)
             
            
    def tc_product_get(self,cr,uid,oid,product_ids,context=None):
        product_obj = self.pool.get("product.product")                
        res = product_obj.read(cr, uid, product_ids, ["id","name","needs_measure","has_sn"], context=context)
        return res
    
    def tc_product_by_code(self,cr,uid,oid,product_code,profile_id=None,context=None):
        product_obj = self.pool.get("product.product")
        product_ids = None
        # 
        if profile_id:
            product_ids = product_obj.search(cr, uid, [("code_profile_id","=",profile_id),("code_value","=",product_code)])
        else:
            product_ids = product_obj.search(cr, uid, [("ean13","=", product_code)],context=context)
        #   
        res =  self.tc_product_get(cr, uid, oid, product_ids, context)
        return res                
    
    def tc_category_main_ids(self,cr,uid,oid,context=None):
        system = self.browse(cr, uid, oid, context)
        return [c.id for c in system.product_category_ids]
    
    def tc_product_list_get(self,cr,uid,oid,category_id=None,context=None):
        category_ids = category_id and [category_id] or self.tc_category_main_ids(cr, uid, oid, context)
        product_obj = self.pool.get("product.product")
        product_ids = product_obj.search(cr,uid,[("categ_id","child_of",category_ids),("active","=",True),("sale_ok","=",True)])    
        res = self.tc_product_get(cr, uid, oid, product_ids, context)
        return res 
            
    def tc_category_name_get(self,cr,uid,category_ids,context=None):
        category_obj = self.pool.get("product.category")
        res = []
        for category in category_obj.browse(cr,uid,category_ids,context=context):
            res.append((category.id,category.name))
        return res            
    
    def tc_category_main_get(self,cr,uid,oid,context=None):
        category_obj = self.pool.get("product.category")
        system = self.browse(cr, uid, oid, context)
        main_category_ids = [c.id for c in system.product_category_ids]
        category_ids = category_obj.search(cr,uid,[("id","in",main_category_ids)],context)
        return self.tc_category_name_get(cr,uid,category_ids,context=context)    
  
    def tc_category_sub_get(self,cr,uid,oid,parent_category_id,context=None):
        category_obj = self.pool.get("product.category")        
        category_ids = category_obj.search(cr,uid,[("parent_id","=",parent_category_id)],context)        
        return self.tc_category_name_get(cr,uid,category_ids,context=context) 
    
    def tc_category_parent_get(self,cr,uid,oid,category_id,context=None):
        category_obj = self.pool.get("product.category")
        system = self.browse(cr, uid, oid, context)
        main_category_ids = [c.id for c in system.product_category_ids]                        
        category = category_obj.browse(cr,uid,category_id)
        while category:            
            parent_category = category.parent_id
            if parent_category and parent_category.id in main_category_ids:               
                return {
                    "parent_category_id" : parent_category.id,
                    "category_id" : category.id
                }         
            category=parent_category
        return {}
                 
    def tc_cash_statement_get(self,cr,uid,oid,statement_id,context=None):
        statement_obj = self.pool.get("account.bank.statement")
        statement = statement_obj.browse(cr,uid,statement_id,context=context)
        if statement:
            res = self._tc_statement_status_get(cr, uid, statement, context)
            starting_details = []
            balance_start_is = 0.0
            for detail in statement.starting_details_ids:
                starting_details.append(self._tc_cash_detail_get(cr, uid, detail))
                balance_start_is += detail.subtotal
            res["starting_details"]=starting_details
            res["balance_start_is"]=balance_start_is
            
            ending_details = [] 
            balance_end_is = 0.0
            for detail in statement.ending_details_ids:
                ending_details.append(self._tc_cash_detail_get(cr, uid, detail))
                balance_end_is += detail.subtotal                
            
            res["ending_details"]=ending_details
            res["balance_end_should"]=statement.balance_end
            res["balance_end_is"]=balance_end_is
            res["difference"]=balance_end_is-statement.balance_end
            return res        
        return  {}
    
    
    def tc_cash_statement_start(self,cr,uid,oid,context=None):
        system=self._tc_system_get(cr, uid, oid, context)
        journal = system.cash_journal_id
        statement_obj = self.pool.get("account.bank.statement")
        statement_detail_obj = self.pool.get("account.cashbox.line")
        statement_ids = statement_obj.search(cr,uid,[("state","!=","confirm"),("journal_id","=",journal.id)],context=context)
        
        if len(statement_ids) > 1:
            raise osv.except_osv(_("Error"), _("There are more than one Cash Statement active for Journal %s") % (journal.name,))
        
        statement_id = statement_ids and statement_ids[0] or None
        if not statement_id:
            cr.execute("SELECT id FROM account_bank_statement s WHERE s.state='confirm' AND s.journal_id=%s ORDER BY ID DESC LIMIT 1", (journal.id,))            
            last_statement_ids = [r[0] for r in cr.fetchall()]
            details=[]
            if last_statement_ids:
                last_statement_id = last_statement_ids[0]              
                detail_ids =  statement_detail_obj.search(cr,uid,[("ending_id","=",last_statement_id)],context=context)
                for detail in statement_detail_obj.read(cr,uid,detail_ids,["pieces","number"]):
                    details.append((0,0,{
                        "pieces" : detail["pieces"],
                        "number" : detail["number"]
                    }))                                                        
            
            statement_obj.create(cr, uid, {
                         "journal_id" : journal.id,
                         "starting_details_ids" : details,
                         "ending_details_ids" : []
            },context)            
        return self.tc_status_get(cr, uid, oid, context=context)
        
    def tc_cash_statement_open(self,cr,uid,oid,statement_id,context=None):
        statement_obj = self.pool.get("account.bank.statement")
        statement = statement_obj.browse(cr,uid,statement_id,context=context)
        if not statement:
            raise osv.except_osv(_("Error"), _("There is no Cash Statement with ID %d") % (statement_id,))
        if statement.state != "draft":
            raise osv.except_osv(_("Error"), _("Only Statement in Draft State could opened"))                
        statement_obj.button_open(cr,uid,[statement.id],context=context)            
        return self.tc_status_get(cr, uid, oid, context=context)
    
    def tc_cash_statement_undo(self,cr,uid,oid,statement_id,context=None):
        statement_obj = self.pool.get("account.bank.statement")
        statement = statement_obj.browse(cr,uid,statement_id,context=context)
        if statement.state=="draft":            
            statement_obj.unlink(cr,uid,[statement.id],context=context)
        elif statement.state=="open":
            statement_detail_obj = self.pool.get("account.cashbox.line")
            statement_detail_obj.unlink(cr,uid,[o.id for o in statement.ending_details_ids],context=context)
        return self.tc_status_get(cr, uid, oid, context)
        
    
    def tc_cash_statement_end(self,cr,uid,oid,statement_id,context=None):
        statement_obj = self.pool.get("account.bank.statement")
        statement = statement_obj.browse(cr,uid,statement_id,context=context)
        if not statement:
            raise osv.except_osv(_("Error"), _("There is no Cash Statement with ID %d") % (statement_id,))
        if statement.state != "open":
            raise osv.except_osv(_("Error"), _("Only Statement in Open state could be finished"))
        
        #
        self._tc_cleanup(cr, uid, oid, statement_id, context)
        #        
        #create ending details
        
        if not statement.ending_details_ids:
            ending_details = []            
            starting_details = statement.starting_details_ids                        
            if not starting_details:
                ending_details.append((0,0,statement_obj._get_cash_close_box_lines(cr, uid, context=context)))
            else:
                ending_details=[]
                for detail in starting_details:
                    ending_details.append((0,0,{
                        "pieces" : detail.pieces,
                        "number" : 0
                    }))
            statement_obj.write(cr,uid,[statement.id], {"ending_details_ids" : ending_details })
        return self.tc_status_get(cr, uid, oid, context=context)
                
    def tc_cash_statement_close(self,cr,uid,oid,statement_id,context=None):
        statement_obj = self.pool.get("account.bank.statement")
        statement = statement_obj.browse(cr,uid,statement_id,context=context)
        if not statement:
            raise osv.except_osv(_("Error"), _("There is no Cash Statement with ID %d") % (statement_id,))
        if statement.state != "open":
            raise osv.except_osv(_("Error"), _("Only Statement in Open state could be confirmed"))        
        statement_obj.button_confirm_cash(cr,uid,[statement.id],context=context)
        return self.tc_status_get(cr, uid, oid, context=context)
    
    def tc_cash_statement_print(self,cr,uid,oid,statement_id,context=None):
        system=self._tc_system_get(cr, uid, oid, context)
        printer=system.report_printer_id
        if printer:            
            if printer.type == "local":
                helper.printReport(cr, uid, "at_pos.cashbox", "account.bank.statement", [statement_id], printer=printer.name, context=context)
        return True    
    
    def tc_cash_statement_line_delete(self,cr,uid,oid,statement_id,line_id,context=None):
        line_obj = self.pool.get("account.cashbox.line")
        line_ids = line_obj.search(cr,uid,[("id","=",line_id),"|",("starting_id","=",statement_id),("ending_id","=",statement_id)],context=context,limit=1)
        if line_ids:
            line_obj.unlink(cr,uid,line_ids,context=context)
        return self.tc_cash_statement_get(cr, uid, oid, statement_id, context=context)
        
    def tc_cash_statement_line_modify(self,cr,uid,oid,statement_id,line_id,value,amount,context=None):
        statement_obj = self.pool.get("account.bank.statement")
        line_obj = self.pool.get("account.cashbox.line")
        #
        statement = statement_obj.browse(cr,uid,statement_id,context=context)        
        line_ids = None
        #
        statement_field=(statement.state == "draft" and "starting_id") or (statement.state == "open" and "ending_id") or None
        if statement_field:
            line_ids = line_obj.search(cr,uid,[(statement_field,"=",statement_id),("pieces","=",value)])
            if line_ids:
                line_obj.write(cr,uid,line_ids,{"number":amount},context=context)
            else:
                line_obj.create(cr,uid,{
                            statement_field : statement_id,
                            "pieces" : value,
                            "number" : amount
                        })
        return self.tc_cash_statement_get(cr, uid, oid, statement_id, context=context)
                
        
    def tc_order_create(self,cr,uid,oid,context=None):
        statement_obj = self.pool.get("account.bank.statement")        
        order_obj = self.pool.get("pos.order")
        system=self._tc_system_get(cr, uid, oid, context)
        journal = system.cash_journal_id
        
        # check for open account_cash_statement
        statement_ids = statement_obj.search(cr,uid,[("state","=","open"),("journal_id","=",journal.id)],context=context)
        if statement_ids:            
            statement = statement_obj.browse(cr,uid,statement_ids[0],context)
            order_vals = { "statement_id" : statement.id, 
                           "system_id" : system.id
                        }
            order_id = order_obj.create(cr,uid,order_vals,context=context)
            return self.tc_order_get(cr, uid, oid, order_id, context)
     
        raise osv.except_osv(_("Error"), _("Cannot create order in closed cash statement for journal %s") % (journal.name,))        
         
            
    def tc_order_get(self,cr,uid,oid,order_id,context=None):        
        order_obj = self.pool.get("pos.order")
        order = order_obj.browse(cr,uid,order_id,context=context)
        if order:
            res = self._tc_order_status_get(cr, uid, order, context)
            #
            res["total"]=order.amount_total
            if order.partner_id:
                res["partner"]=self._tc_partner_get(cr,uid,order.partner_id,context)
            
            #
            lines = []
            discount = None
            discount_count = 0
            discount_amount = 0
            order_lines = order.lines            
            for line in order_lines:
                line_res = tcm.tcm_name(line)                 
                #
                brutto = line.price_brutto
                subtotal_brutto = line.subtotal_brutto                
                line_res["product"]=self.tc_product_get(cr,uid,oid,line.product_id.id,context=context)
                line_res["qty"]=line.qty      
                line_res["brutto"]=brutto
                line_res["subtotal_brutto"]=subtotal_brutto
                line_res["uom"]=tcm.tcm_name(line.product_id.uom_id)
                #
                if line.serial_number:
                    line_res["serial_number"]=line.serial_number
                #
                if line.discount:                                            
                    if discount == line.discount:                       
                        discount_count+=1
                    else:
                        discount = line.discount
                        discount_count=1
                    line_discount_amount=subtotal_brutto-brutto
                    discount_amount+=line_discount_amount
                    line_res["discount"]=line.discount
                    line_res["discount_amount"]=line_discount_amount
                                                    
                #                
                lines.append(line_res)
                #
            if lines:
                res["lines"]=lines          
                if discount and discount_count == len(order_lines):
                    res["discount"]=discount
                    res["discount_amount"]=discount_amount
            #   
            payment_lines = self._tc_validate_payment(cr, uid, order_id, context)
            if payment_lines:
                res["payment"]=payment_lines
            return res
        return {}
        
    def tc_order_undo(self, cr, uid, oid, order_id, context=None):
        order_obj = self.pool.get("pos.order")
        order = order_obj.browse(cr,uid,order_id,context=context)
        if order and order.state=="draft":            
            order_obj.unlink(cr,uid,[order_id],context=context)
        return self.tc_status_get(cr, uid, oid, context)
        
    def tc_order_line_delete(self,cr,uid,oid,order_id,line_id,context=None):
        line_obj = self.pool.get("pos.order.line")
        line_obj.unlink(cr,uid,line_id,context=context)
        return self.tc_order_get(cr, uid, oid, order_id, context)
      
    def tc_order_partner_change(self,cr,uid,oid,order_id,partner_id,context=None):
        order_obj = self.pool.get("pos.order")
        chg_values = order_obj.onchange_partner_pricelist(cr,uid,[order_id],partner_id,context=context)["value"]
        chg_values["partner_id"]=partner_id
        order_obj.write(cr,uid,order_id,chg_values,context=context)        
        #
        payment_obj = self.pool.get("pos.order.payment")
        payment_ids  = payment_obj.search(cr,uid,[("order_id","=",order_id)])
        if payment_ids:
            payment_obj.unlink(cr,uid,payment_ids,context)
            self.tc_payment_start(cr, uid, oid, order_id, context)            
        #
        return self.tc_order_get(cr, uid, oid, order_id, context)
   
    def tc_order_next(self, cr, uid, oid, order_id, create_new=False, context=None):
        order = self.pool.get("pos.order").browse(cr,uid,order_id,context=context)
        cr.execute("SELECT id FROM pos_order WHERE id > %s AND statement_id = %s AND system_id = %s ORDER BY ID ASC LIMIT 1",(order_id,order.statement_id.id,oid))
        order_ids = [r[0] for r in cr.fetchall()]        
        if order_ids:
            return self.tc_order_get(cr, uid, oid, order_ids[0], context)
        elif create_new:
            return self.tc_order_create(cr, uid, oid, context)
        return self.tc_order_get(cr, uid, oid, order_id, context)
    
    def tc_order_privious(self, cr, uid, oid, order_id, context=None):
        order = self.pool.get("pos.order").browse(cr,uid,order_id,context=context)                
        cr.execute("SELECT id FROM pos_order WHERE id < %s AND statement_id = %s AND system_id = %s ORDER BY ID DESC LIMIT 1",(order_id,order.statement_id.id,oid))
        order_ids = [r[0] for r in cr.fetchall()]                
        if order_ids:
            return self.tc_order_get(cr, uid, oid, order_ids[0], context)
        return self.tc_order_get(cr, uid, oid, order_id, context)
    
    def tc_order_pay(self, cr, uid, oid, order_id, print_order=False, new_order=False, context=None):
        # lock journals
        payment_obj = self.pool.get("pos.order.payment")        
        payment_ids  = payment_obj.search(cr,uid,[("order_id","=",order_id)])
        if not payment_ids:
            return self.tc_order_get(cr, uid, oid, order_id, context=context)
        #
        order_obj = self.pool.get("pos.order")        
        order = order_obj.browse(cr, uid, order_id, context=context)
        if order.state in ("paid","closed"):
            raise osv.except_osv(_("Error"), _("Finished Orders could not be paid again"))
        
        system= self._tc_system_get(cr, uid, oid, context)
        cash_journal = system.cash_journal_id
        amount = 0.0
        #
        statement_obj = self.pool.get("account.bank.statement")
        statement_ids = statement_obj.search(cr,uid,[("journal_id","=",cash_journal.id),("state","=","open")],limit=1,context=context)        
        statement = statement_ids and statement_obj.browse(cr,uid,statement_ids[0],context) or None
        if not statement:
            raise osv.except_osv(_("Error"), _("No Cash Statement open for payment"))
        #
        journal_ids = self._tc_journal_ids(cr, uid, system, context=context)
        cr.execute("SELECT id FROM account_bank_statement s WHERE s.id IN %s FOR UPDATE",(tuple(journal_ids),))
        #        
        for payment in payment_obj.browse(cr, uid, payment_ids, context=context):
            payment_amount = payment.amount                        
            amount+=payment_amount
            payment_data = { "is_acc" : False,
                             "payment_name" : _("Payment"),
                             "payment_date" : util.currentDate(),
                             "invoice_wanted" : False,
                             "pricelist_id" : order.pricelist_id.id or None,
                             "partner_id" : order.partner_id.id or None,
                             "product_id" : None,
                             "amount" : payment_amount,
                             "num_sale" : None                             
                            }
                        
            if payment.type == "cash":
                payment_data["journal"]=cash_journal.id
            elif payment.type == "balance":
                if not system.balance_journal_id:
                    raise osv.except_osv(_("Error"), _("No Balance journal defined for POS System %s") % (system.name,))
                self._tc_child_statement_get(cr,uid,oid,statement,system.balance_journal_id,context)
                payment_data["journal"]=system.balance_journal_id.id            
            elif payment.type == "voucher":
                if not system.voucher_journal_id:
                    raise osv.except_osv(_("Error"),_("No Voucher journal defined for POS System %s") % (system.name,))
                self._tc_child_statement_get(cr,uid,oid,statement,system.voucher_journal_id,context)
                payment_data["journal"]=system.voucher_journal_id.id
            
            statement_line_id = order_obj.add_payment(cr,uid,order_id,payment_data,context=context)
            payment_obj.write(cr, uid, payment.id, { "statement_line_id" : statement_line_id })
                
        if round(order.payment_all,2) != round(amount,2):
            raise osv.except_osv(_("Error"), _("Amount of sale and payment is different"))

        order_ids = [order_id]
        if order_obj.test_paid(cr,uid,order_ids):
            order_obj.action_paid(cr, uid, order_ids, context=context)
            order_obj.write(cr, uid, order_ids, {'state':'paid'}, context=context)
            #
            if print_order:
                try:
                    self.tc_print_bon(cr, uid, oid, order_id, context)
                except:
                    pass
                
        if new_order:
            return self.tc_order_create(cr, uid, oid, context=context)
        #                    
        return self.tc_order_get(cr, uid, oid, order_id, context=context) 
     
    def tc_order_discount(self,cr,uid,oid,order_id,discount,context=None):
        line_obj = self.pool.get("pos.order.line")
        line_ids = line_obj.search(cr,uid,[("order_id","=",order_id)])
        if line_ids:
            line_obj.write(cr,uid,line_ids,{ "discount" : discount },context=context)
        return self.tc_order_get(cr, uid, oid, order_id, context=context)
     
    def tc_order_modify(self,cr,uid,oid,order_id,line_id,product_id,qty,discount,serial_number,price_unit,context=None):
        line_obj = self.pool.get("pos.order.line")
        #
        order_obj = self.pool.get("pos.order")
        order_values = order_obj.read(cr, uid, order_id, ["pricelist_id","company_id","state"], context)        
        pricelist_id = order_values["pricelist_id"]
        company_id = order_values["company_id"]
        order_state = order_values["state"]
        
        pricelist_id = pricelist_id and pricelist_id[0] or None
        company_id = company_id and company_id[0] or None
        discount = discount or 0.0
        
        if order_state not in ("draft","payment","advance"):
            raise osv.except_osv(_("Error"), _("Closed Orders could not be changed"))
        
        values = { "order_id" : order_id,
                   "company_id" : company_id,
                   "product_id" : product_id,
                   "qty" : qty,
                   "discount" : discount,
                   "serial_number" : serial_number
                 }              
        line_ids = line_id and [line_id] or []
        chg_values = line_obj.onchange_product_id(cr,uid,line_ids,pricelist_id,product_id,qty)["value"]        
        #
        #if isinstance(price_unit, (int,float)):
        #    chg_values["price_unit"]=price_unit        
        #
        price = chg_values["price_unit"]
        #
        chg_values.update(line_obj.onchange_qty(cr,uid,line_ids,discount,qty,price,context=context)["value"])
        chg_values.update(line_obj.onchange_discount(cr,uid,line_ids,discount,price)["value"])        
        
        values.update(chg_values)
        if line_ids:
            line_obj.write(cr,uid,line_ids,values,context=context)
        else:
            line_id = line_obj.create(cr,uid,values,context=context)           
        
        res = self.tc_order_get(cr, uid, oid, order_id, context)
        res["modified_line_id"]=line_id
        return res
                   
    def tc_payment_start(self, cr, uid, oid, order_id, context=None):
        payment_obj = self.pool.get("pos.order.payment")
        cash_ids = payment_obj.search(cr,uid,[("order_id","=",order_id),("type","=","cash")])
        cash_id = cash_ids and cash_ids[0] or None
        if not cash_id:
            payment_values = { "order_id" : order_id,
                               "type" : "cash"
                             }
            cash_id = payment_obj.create(cr,uid,payment_values,context=context)
        res = self.tc_order_get(cr, uid, oid, order_id, context)
        res["modified_payment_id"]=cash_id
        return res
    
    def tc_payment_balance_start(self, cr, uid, oid, order_id, context=None):
        payment_obj = self.pool.get("pos.order.payment")
        payment_ids = payment_obj.search(cr,uid,[("order_id","=",order_id),("type","=","balance")])
        payment_id = payment_ids and payment_ids[0] or None
        if not payment_id:
            order_obj = self.pool.get("pos.order")
            order = order_obj.browse(cr,uid,order_id,context=context)            
            if order and order.partner_id:
                balance = order.partner_id.calculated_balance                
                if balance:
                    payment_values = { 
                               "order_id" : order_id,
                               "type" : "balance",
                               "amount" : min(order.payment_residual or order.payment_cash,balance)
                               }
                    payment_id = payment_obj.create(cr,uid,payment_values,context=context)
       
        res = self.tc_order_get(cr, uid, oid, order_id, context)
        if payment_id: 
            res["modified_payment_id"]=payment_id
        return res
                    
    def tc_payment_delete(self, cr, uid, oid, order_id, payment_id, context=None):
        payment_obj = self.pool.get("pos.order.payment")
        payment_obj.unlink(cr,uid,payment_id)
        return self.tc_order_get(cr, uid, oid, order_id, context)
    
    def tc_payment_modify(self, cr, uid, oid, order_id, payment_id, payment_name, payment_type, payment_amount, payment_balance, context=None):
        payment_obj = self.pool.get("pos.order.payment")        
        if payment_type != "cash":
            payment_values = { "order_id" : order_id,
                               "type" : payment_type,
                               "name" : payment_name,
                               "amount" : payment_amount,
                               "balance" : payment_balance
                               }
            
            if not payment_id:
                payment_id = payment_obj.create(cr,uid,payment_values,context=context)
            else:                    
                payment_obj.write(cr,uid,payment_id,payment_values,context=context)
                
        res =  self.tc_order_get(cr, uid, oid, order_id, context)
        res["modified_payment_id"]=payment_id
        return res
                              
    def tc_status_get(self,cr,uid,oid,context=None):  
        system=self._tc_system_get(cr, uid, oid, context)
                
        user_obj = self.pool.get("res.users")
        statement_obj = self.pool.get("account.bank.statement")        
        order_obj = self.pool.get("pos.order")
        product_code_obj = self.pool.get("product.code.profile")
          
        journal = system.cash_journal_id
        company = journal.company_id
        currency = company.currency_id
        #        
        res = tcm.tcm_name(system)
        res["cash_journal"]=tcm.tcm_name(journal)
        res["balance_journal"]=tcm.tcm_name(system.balance_journal_id)
        res["voucher_journal"]=tcm.tcm_name(system.voucher_journal_id)
        res["company"]=tcm.tcm_name(company)
        res["user"]=user_obj.whoami(cr,uid,context=context)
        res["state"]=tcm.STATE_CASH_STMT_CLOSED
        #
        product_code_ids = product_code_obj.search(cr,uid,[],context=context)
        if product_code_ids:
            product_code_profiles = []
            for profile in product_code_obj.browse(cr,uid,product_code_ids,context=context):
                product_code_profiles.append(self._tc_product_code_profile_get(cr, uid, profile, context=context))        
            res["product_code_profiles"]=product_code_profiles
            
        #
        res["dp_sale"] = format.LangFormat(cr, uid, context=context, dp="Point Of Sale").digits()
        res["dp_uom"] = format.LangFormat(cr, uid, context=context, dp="Product UoM").digits()        
        #
        display = {
           "currency" : (currency and currency.symbol or currency.name) or "",
           "system" :  "%s / %s" % (company.name,system.name),
           "name" : res["user"]["name"],
           "state" : _("Online"),
           "info" :  None,
           "total" : None        
        }
        res["display"]=display        
                
        # check for open account_cash_statement
        statement_ids = statement_obj.search(cr,uid,[("journal_id","=",journal.id)],limit=1,context=context)
        if statement_ids:
            statement = statement_obj.browse(cr,uid,statement_ids[0],context)
            #
            cash_statement_res=self.tc_cash_statement_get(cr, uid, oid, statement.id, context)                                     
            res["cash_statement"]=cash_statement_res
            #      
            if statement.state == "confirm":
                res["state"]=tcm.STATE_CASH_STMT_CLOSED
            else:               
                if statement.state == "draft":
                    res["state"]=tcm.STATE_CASH_STMT_OPENING                                
                else:
                    if cash_statement_res.get("ending_details"):
                        res["state"]=tcm.STATE_CASH_STMT_BALANCING
                    else:
                        res["state"]=tcm.STATE_ORDER           
                        cr.execute("SELECT id FROM pos_order o WHERE o.statement_id = %s AND o.system_id = %s ORDER BY ID DESC LIMIT 1", (statement.id,oid))
                        order_ids = [r[0] for r in cr.fetchall()]                         
                        order_id = order_ids and order_ids[0]
                        if not order_id:
                            order_vals = { "statement_id" : statement.id, 
                                           "system_id" : system.id
                                          }
                            order_id = order_obj.create(cr,uid,order_vals,context=context)
                            
                        if order_id:
                            res["order"]=self.tc_order_get(cr, uid, oid, order_id, context)
        else:
            res["state"]=tcm.STATE_CASH_STMT_NONE                                    
        #            
        return res
    
    def tc_login(self,cr,uid,system,context=None):
        ids = self.search(cr, uid, [("name","=",system)])
        if not ids:
            raise osv.except_osv(_("Error"), _("No POS System %s found") % (system,))
        return self.tc_status_get(cr, uid, ids[0], context)
    
    def tc_print(self, cr, uid, oid, report_name, res_model, res_ids, context=None):
        system=self._tc_system_get(cr, uid, oid, context)
        if system and system.report_printer_id:
            helper.printReport(cr, uid, report_name, res_model, res_ids, system.report_printer_id.name, context=context)
        return True
     
    def tc_esc_print(self, cr, uid, printer, order_id, context=None):
        tax_obj = self.pool.get("account.tax")              
        order_obj = self.pool.get("pos.order")
        order = order_obj.browse(cr, uid, order_id, context)
        f = format.LangFormat(cr,uid,context,dp="Point Of Sale")
        
        col1 = 0.5
        col2 = 0.31
        col2_1 = 0.17
        col2_2 = 0.15
        col3 = 0.20
        
        currency = (order.company_id and order.company_id.currency_id and order.company_id.currency_id.name) or ""
               
        printer = Escpos(printer)
        printer.cashdraw(2)                
        printer.hw("INIT")                
        printer.set(align="center",height=2,width=2)
        printer.text("\n")
            
        header = order.company_id.escpos_header
        if header:
            first = True
            for line in header.split("\n"):
                if first:                                                
                    first = False
                    printer.text(line+"\n")
                    printer.set(align="center",height=1,width=1)
                else:
                    printer.text(line+"\n")                            
         
        printer.set(align='left',height=1,width=1)           
        printer.set(align='left',height=1,width=1)
        printer.text("\n\n\n")
        printer.ltext(order.name,0.5)
        printer.rtext(f.formatLang(order.date_order,date_time=True),0.5)
        printer.text("\n\n")
                                          
        for line in order.lines:                        
            product = line.product_id
            product_name = product.name or line.name or ''
            printer.ltext(product_name,col1)
                                
            uom = product and ( product.uos_id or product.uom_id ) or None 
            uomtxt = uom and (uom.code or uom.name) or ""                                        
            qty = f.formatLang(line.qty,dp="Product UoM")
            subtotal = f.formatLang(line.subtotal_brutto or 0.0)
            
            
            if product and not product.income_pdt and not product.expense_pdt:
                printer.rtext(qty,col2_1)
                printer.rtext(uomtxt,col2_2)
            else:
                printer.rtext("",col2_1)
                printer.rtext("",col2_2)
                
            printer.rtext(subtotal,col3)
            printer.text("\n")
            if line.discount:
                printer.text(_("  - %s %% Discount\n") % (line.discount,))
        
        printer.line()
        printer.ltext(_("Total (Brutto)"),col1)
        printer.rtext(currency,col2)
        printer.rtext(f.formatLang(order.amount_total),col3)
        printer.text("\n")
        
        taxes = {}
        for tax_id, tax_amount in order_obj._tax_amount(cr,uid,order_id,context).items():
            tax = tax_obj.browse(cr,uid,tax_id,context)
            t_amount = taxes.get(tax.name,0.0)
            t_amount += tax_amount
            taxes[tax.name] = t_amount            
            
        for tax_name, tax_amount in taxes.items():
            printer.ltext(_("incl. %s") % tax_name,col1)
            printer.rtext(currency,col2)
            printer.rtext(f.formatLang(tax_amount),col3)
            printer.text("\n")
                
#        if order.partner_id:
#            partner = order.partner.id
#            printer.text("\n\n")
#            printer.text(partner.name)
#            printer.text("\n")            
        
        printer.text("\n")     
        printer.text(_("Payments"))    
        printer.text("\n")                   
        for payment in order.payment_ids:
            payment_line = []
            if payment.type == "cash":
                payment_line.append(_("Bar"))
            elif payment.type == "balance":
                payment_line.append(_("Balance"))
            elif payment.type == "voucher":
                payment_line.append(_("Voucher"))            
            #
            if payment.name:
                payment_line.append(payment.name)
            
            if payment.balance:
                payment_line.append(f.formatLang(payment.balance))
                                    
            printer.ltext(" ".join(payment_line),col1)
            printer.rtext(currency,col2)
            printer.rtext(f.formatLang(payment.amount),col3)
            printer.text("\n")
            
        partner = order.partner_id
        if partner:
            printer.text("\n")
            printer.text(_("Calculated Balance"))
            printer.text("\n")
            printer.ltext(partner.name,col1)
            printer.rtext(currency,col2)
            printer.rtext(f.formatLang(partner.calculated_balance),col3)
            printer.text("\n")
        
        printer.text("\n")                
        printer.cut()
        printer.close()
        return True
    
    def tc_esc_cashdrawer_open(self, cr, uid, printer, context=None):
        printer = Escpos(printer)
        printer.hw("INIT")    
        printer.cashdraw(2)                
        printer.close()
        return True    
               
    def tc_print_bon(self, cr, uid, oid, order_id, context=None):       
        system=self._tc_system_get(cr, uid, oid, context)
        printer=system.bon_printer_id
        if printer:
            if printer.type == "esc_net":
                self.tc_esc_print(cr, uid, printer.name, order_id, context=context)
            elif printer.type == "local":
                helper.printReport(cr, uid, "at_pos.bon", "pos.order", [oid], printer=printer.name, context=context)
        return True
    
    def tc_print_cashdrawer_open(self, cr, uid, oid, context=None):
        system=self._tc_system_get(cr, uid, oid, context)
        printer=system.bon_printer_id
        if printer:
            if printer.type == "esc_net":
                self.tc_esc_cashdrawer_open(cr, uid, printer.name, context=context)
            elif printer.type == "local":
                helper.printText(cr, uid, " ", printer.name, context)
        return True
                 
    
    _columns = {
        "name" : fields.char("Name",size=64,required=True,select=True),     
        "bon_printer_id" : fields.many2one("at_pos.pos_printer","BON Printer"),
        "report_printer_id" : fields.many2one("at_pos.pos_printer","Report Printer",domain=[("type","=","local")]),
        "cash_journal_id" : fields.many2one("account.journal","Cash Journal",domain=[("type","=","cash")],required=True),        
        "balance_journal_id" : fields.many2one("account.journal","Balance Journal",domain=[("type","=","cash"),("auto_cash","=",True),("balance_credit","=",True)],
                                               help="Balance Journal for balance the order with asset or a credit note. Auto opening must be enabled for this journal " 
                                                " and balance_credit must also be enabled"),
        "voucher_journal_id" : fields.many2one("account.journal","Voucher Journal",domain=[("type","=","cash")],
                                               help="Journal for vouchers"),
        "product_category_ids" : fields.many2many("product.category","pos_system_product_category_rel","system_id","category_id",string="Product Categories")
    }
    
    _name = "at_pos.pos_system"
    _description = "POS System"
pos_system()