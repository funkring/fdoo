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

from openerp.osv import osv, fields
from openerp.tools.translate import _
from at_base import helper
from at_base import format
from escpos import Escpos
import decimal_precision as dp


#Override pos_receipt wizard
class pos_receipt(osv.osv_memory):
    _inherit = 'pos.receipt'
    _description = 'Point of sale receipt'

    def print_report(self, cr, uid, ids, context=None):
        """
        To get the date and print the report
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return : retrun report
        """
        if context is None:
            context = {}
        
        order_obj = self.pool.get("pos.order")        
        if order_obj.print_bon(cr,uid,context.get('active_id', None),context=context):            
            return { "type" : "ir.actions.act_window_close" }
        else:          
            datas = {'ids': context.get('active_ids', [])}
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'at_pos.bon',            
                'datas': datas,
            }
pos_receipt()


#Override pos_make_payment wizard
class pos_make_payment(osv.osv_memory):    
    _inherit = "pos.make.payment"
    
    def print_report(self, cr, uid, ids, context=None):
        """
         @summary: To get the date and print the report
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return : retrun report
        """
        if context is None:
            context = {}
            
        make_payment = self.browse(cr, uid, ids, context)[0] or None       
        if make_payment:
            pos_order_obj = self.pool.get('pos.order')
            active_id = context.get('active_id')
            if pos_order_obj.print_bon(cr,uid,active_id,context=context):
                return { "type" : "ir.actions.act_window_close" }
                             
        active_id = context.get('active_id', [])
        datas = {'ids' : [active_id]}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'at_pos.bon',
            'datas': datas,
        }         
pos_make_payment()

#override order line
class pos_order_line(osv.osv):
    """ Extend the Order Line """
      
    def _amount_brutto(self, cr, uid, ids, field_names, arg, context=None):       
        res = {} 
        account_tax_obj = self.pool.get('account.tax')
        currency_obj =  self.pool.get('res.currency')
                
        for line in self.browse(cr, uid, ids, context):            
            taxes = [t for t in line.product_id.taxes_id]
            cur = line.order_id.pricelist_id.currency_id
            res_line = {}
                        
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            computed_taxes = account_tax_obj.compute_all(cr, uid, taxes, price, line.qty)
            res_line["subtotal_brutto"] = currency_obj.round(cr, uid, cur, computed_taxes['total_included'])
            
            computed_taxes = account_tax_obj.compute_all(cr, uid, taxes, line.price_unit, 1)
            res_line["price_brutto"] = currency_obj.round(cr, uid, cur, computed_taxes['total_included'])
            res[line.id] = res_line
            
        return res
            
            
    def pos_modify_line(self, cr, uid, product_id, qty, discount, order):
        # search pricelist_id        
        order_obj = self.pool.get('pos.order')
        order = order_obj.browse(cr,uid,order)
        pricelist = order.pricelist_id
        if not pricelist:
            return False

        new_line = True 

        # search price product
        product_obj = self.pool.get('product.product')
        product = product_obj.browse(cr,uid,product_id)
        price = self.price_by_product(cr, uid, 0, pricelist.id, product.id, 1)
        line = None
        
        if not product.needs_measure:
            order_line_ids = self.search(cr, uid, [('product_id', '=', product.id), ('order_id', '=' ,order.id),('discount','=',discount)])
            lines = self.browse(cr, uid, order_line_ids)            
            if lines:
                line = lines[0]
                new_line = False
                qty += line.qty
        elif qty < 0.0:
            order_line_ids = self.search(cr, uid, [('product_id', '=', product.id), ('order_id', '=' ,order.id),('qty','=',(-qty)),('discount','=',discount)])
            lines = self.browse(cr, uid, order_line_ids)            
            if lines:
                line = lines[0]
                new_line = False
                qty += line.qty
            
        if new_line:
            if qty:            
                vals = {'product_id': product.id,
                        'price_unit': price,
                        'qty': qty,
                        'name': product.name,
                        'order_id': order.id,
                        'discount' : discount
                }
                line_id = self.create(cr, uid, vals)
                if not line_id:
                    raise osv.except_osv(_('Error'), _('Create line failed !'))
        else:
            if qty:
                vals = {
                    'qty': qty,
                    'price_unit': price,                    
                }
                if not self.write(cr, uid, [line.id], vals):
                    raise osv.except_osv(_('Error'), _('Modify line failed !'))                
            else:
                self.unlink(cr, uid, [line.id])

        return True
        
        
    def pos_scan_product(self,cr,uid,ean,qty,discount,order):        
        product_obj = self.pool.get('product.product')
        product_id = product_obj.search(cr, uid, [('ean13','=', ean)])
        if not product_id:
            return False
    
        return self.pos_modify_line(cr, uid, product_id, qty, discount, order)        

    
    _inherit = "pos.order.line"
    _columns = {                
        "price_brutto" : fields.function(_amount_brutto, multi='amount_brutto',string='Price (Brutto)',store=True,digits_compute=dp.get_precision('Point Of Sale')),
        "subtotal_brutto" : fields.function(_amount_brutto, multi='amount_brutto', string='Total (Brutto)',store=True,digits_compute=dp.get_precision('Point Of Sale'))
    }
pos_order_line()
   

#override order
class pos_order(osv.osv):
    """ Extend the Sales Order for IPad POS System Touch&Cash """
    
    def _payment_other(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT p.order_id,SUM(p.amount) FROM pos_order_payment p "
                   " WHERE p.order_id IN %s "
                   "   AND p.type != 'cash' "
                   " GROUP BY 1 ", (tuple(ids),) )
        
        for row in cr.fetchall():
            res[row[0]]=row[1]                                
        return res
    
    def _payment_cash(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT p.order_id,SUM(p.amount) FROM pos_order_payment p "
                   " WHERE p.order_id IN %s "
                   "   AND p.type = 'cash' "
                   " GROUP BY 1 ", (tuple(ids),) )
        
        for row in cr.fetchall():
            res[row[0]]=row[1]                                
        return res
    
    def _payment_all(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT p.order_id,SUM(p.amount) FROM pos_order_payment p "
                   " WHERE p.order_id IN %s "
                   " GROUP BY 1 ", (tuple(ids),) )
        for row in cr.fetchall():
            res[row[0]]=row[1]                                
        return res
    
    def _payment_residual(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for order in self.browse(cr,uid,ids,context=context):
            res[order.id]=order.amount_total-order.payment_all                             
        return res
    
    def _statement_id_get(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        ids_tuple = tuple(ids)
        
        cr.execute("SELECT o.id, o.statement_id FROM pos_order o WHERE o.id IN %s", (ids_tuple,))
        for row in cr.fetchall():
            res[row[0]]=row[1]
        
        cr.execute("SELECT sl.pos_statement_id, s.id, s.parent_id FROM account_bank_statement_line sl "
                   "  INNER JOIN account_bank_statement s ON s.id = sl.statement_id " 
                   "  WHERE sl.pos_statement_id IN %s "
                   "  GROUP BY 1,2,3 ", (ids_tuple,))
        
        for row in cr.fetchall():
            order_id = row[0]
            statement_id = row[1]
            parent_statement_id = row[2]
            if parent_statement_id:
                res[order_id]=parent_statement_id
            elif statement_id:
                res[order_id]=statement_id
        return res
    
    def _statement_id_set(self, cr, uid, oid, field_name, field_value, arg, context=None):        
        cr.execute("UPDATE pos_order SET statement_id = %s WHERE pos_order.id = %s", (field_value,oid))
        return True
        
    _inherit = "pos.order"  
    _columns = {
        "statement_id" : fields.function(_statement_id_get, type="many2one", obj="account.bank.statement",
                                         string="Cash Statement", 
 store=True,
                                         states={"draft": [("readonly", False)]}, select=True ),
        "system_id" : fields.many2one("at_pos.pos_system","System",states={"draft": [("readonly", False)]}, readonly=True,select=True),
        "payment_ids" : fields.one2many("pos.order.payment", "order_id", "Payment Proposal"),
        "payment_other" : fields.function(_payment_other,type="float",digits_compute=dp.get_precision("Point Of Sale"),string="Payment Other"),
        "payment_cash" : fields.function(_payment_cash,type="float",digits_compute=dp.get_precision("Point Of Sale"),string="Payment Cash"),
        "payment_all" : fields.function(_payment_all,type="float",digits_compute=dp.get_precision("Point Of Sale"),string="Payment All"),
        "payment_residual" : fields.function(_payment_residual,type="float",digits_compute=dp.get_precision("Point Of Sale"),string="Payment Residual"),
        
    }  
    
    def _tax_amount(self,cr,uid,oid,context=None):
        """
        RETURN: {
                tax.id: 0.0
            }
        """    
        res = {}
        tax_obj = self.pool.get("account.tax")
        order = self.browse(cr, uid, oid, context)        
        for line in order.lines:
            product = line.product_id
            taxes = product.taxes_id
            if not taxes:
                continue
            
            tax_calc = tax_obj.compute_all(cr, uid,taxes, line.price_unit * (1-(line.discount or 0.0)/100.0), line.qty,product=product.id)
            for tax in tax_calc["taxes"]:
                tax_id = tax["id"]
                tax_amount = tax.get("amount",0.0)     
                amount = res.get(tax_id,0.0)
                amount += tax_amount
                res[tax_id] = amount
            
        return res
        
    def _select_pricelist(self, cr, uid, context=None):
        """ To get default pricelist for the order
        @param name: Names of fields.
        @return: pricelist ID
        """
        if not context:
            context = {}
        
        pricelist_id = context.get("pricelist_id")
        if not pricelist_id:
            shop_id = context.get("shop_id")
            shop_obj = self.pool.get("sale.shop")
            if not shop_id:
                res = shop_obj.search(cr, uid, [], context=context)
                if res:
                    shop_id = res[0]
            if shop_id:
                shop = shop_obj.browse(cr, uid, shop_id, context=context)
                pricelist_id = shop.pricelist_id and shop.pricelist_id.id or False
                           
        return pricelist_id
    
    
    def _lock_order_lines(self, cr, uid, order):
        try:
            # Must lock with a separate select query because FOR UPDATE can't be used with
            # aggregation/group by's (when individual rows aren't identifiable).
            # We use a SAVEPOINT to be able to rollback this part of the transaction without
            # failing the whole transaction in case the LOCK cannot be acquired.
            cr.execute("SAVEPOINT pos_modify_line")
            cr.execute("SELECT id FROM pos_order "
                       "  WHERE id=%s " 
                       "  FOR UPDATE OF pos_order ", (order,), log_exceptions=False)
            return True
        except Exception:
            # Here it's likely that the FOR UPDATE NOWAIT failed to get the LOCK,
            # so we ROLLBACK to the SAVEPOINT to restore the transaction to its earlier
            # state, we return False as if the products were not available, and log it:
            cr.execute("ROLLBACK TO pos_modify_line")
            return False        
    
    
    def get_journal(self,cr,uid,context=None):
        journal_obj = self.pool.get('account.journal')        
        cr.execute("SELECT DISTINCT journal_id FROM pos_journal_users "
                   "WHERE user_id = %d ORDER BY journal_id"% (uid, ))
        
        j_ids = map(lambda x1: x1[0], cr.fetchall())
        journal = journal_obj.search(cr, uid, [('type', '=', 'cash'), ('id', 'in', j_ids)], context=context)
        journal_id = journal and journal[0] or False        
        return journal_id and journal_obj.browse(cr, uid, journal_id, context) or None
        
    def print_bon(self,cr,uid,oid,context=None):
        # todo print pon       
        journal = self.get_journal(cr, uid, context)
        pos_printer = None
        printer_escpos = False
                
        if journal:        
            pos_printer =  journal.pos_printer
            printer_escpos = journal.printer_escpos
        
        if pos_printer:            
             
            if printer_escpos:  
                tax_obj = self.pool.get("account.tax")              
                pos_order = self.browse(cr, uid, oid, context)
                f = format.LangFormat(cr,uid,context,dp="Point Of Sale")
                
                
                col1 = 0.5
                col2 = 0.31
                col2_1 = 0.17
                col2_2 = 0.15
                col3 = 0.20
                            
                
                
                currency = pos_order.company_id and pos_order.company_id.currency_id and pos_order.company_id.currency_id.name or ""
                       
                printer = Escpos(pos_printer)
                printer.cashdraw(2)                
                printer.hw("INIT")                
                printer.set(align="center",height=2,width=2)
                printer.text("\n")
                    
                header = journal.company_id.escpos_header
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
                printer.ltext(pos_order.name,0.5)
                printer.rtext(f.formatLang(pos_order.date_order,date_time=True),0.5)
                printer.text("\n\n")
                                                  
                for line in pos_order.lines:                        
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
                printer.rtext(f.formatLang(pos_order.amount_total),col3)
                printer.text("\n")
                
                taxes = {}
                for tax_id, tax_amount in self._tax_amount(cr,uid,oid,context).items():
                    tax = tax_obj.browse(cr,uid,tax_id,context)
                    t_amount = taxes.get(tax.name,0.0)
                    t_amount += tax_amount
                    taxes[tax.name] = t_amount            
                    
                for tax_name, tax_amount in taxes.items():
                    printer.ltext(_("incl. %s") % tax_name,col1)
                    printer.rtext(currency,col2)
                    printer.rtext(f.formatLang(tax_amount),col3)
                    printer.text("\n")
                
                printer.text("\n\n")                
                printer.cut()
                printer.close()
                
            else:
                helper.printReport(cr, uid, "at_pos.bon", "pos.order", [oid], printer=pos_printer, context=context)
                
            return True        
        
        return False
   
    
    def open_cashdrawer(self,cr,uid,ids,context=None):
        journal = self.get_journal(cr, uid, context)
        pos_printer = None
        if journal:        
            pos_printer =  journal.pos_printer
            printer_escpos = journal.printer_escpos
            
        # todo open cash drawer       
        if pos_printer:
            if printer_escpos:
                printer = Escpos(pos_printer)
                printer.hw("INIT")    
                printer.cashdraw(2)                
                printer.close()    
            else:        
                helper.printText(cr, uid, " ", pos_printer, context)            
        
        return True
       
    
    def start_cash_box(self,cr,uid,name,context=None):
        journal = self.get_journal(cr, uid, context)
        return {
            "journal_id" : journal.id or False,
            "pricelist_id" : self._select_pricelist(cr, uid, context),        
        }
        
        
    def pos_do_cash(self,cr,uid,oid,context=None):
        if self._lock_order_lines(cr, uid, oid):
            if not context:
                context = {}       
            
            journal_id = context.get("journal_id")
            if not journal_id:
                journal_id = self.get_journal(cr, uid, context)
                        
            order = self.browse(cr, uid, oid, context)
            new_context = context.copy()
            new_context["active_id"]=oid
            new_context["active_model"]="pos.order"
    
            if order.state == "draft":                        
                payment_obj = self.pool.get("pos.make.payment")
                values = payment_obj.default_get(cr,uid,["journal","amount","payment_date","payment_name"],new_context)
                if journal_id:
                    values["journal"] = journal_id
                
                payment_id = payment_obj.create(cr, uid, values, new_context)            
                payment_obj.check(cr,uid,[payment_id],new_context)
            
            else:            
                order_obj = self.pool.get("pos.order")
                order_obj.print_bon(cr,uid,oid,context=new_context)                              
            
        return True

            
    def pos_new_order(self,cr,uid,context=None):
        fields = self.fields_get_keys(cr, uid, context)        
        vals = self.default_get(cr, uid, fields, context)
        return self.create(cr, uid, vals, context)
   
    def pos_order_view(self,cr,uid,oid,context=None,empty_product_id=None):
        res = {}        
        lf_pos = format.LangFormat(cr,uid,context,dp="Point Of Sale")
        lf_uom = format.LangFormat(cr,uid,context,dp='Product UoM')      
        order = self.browse(cr,uid,oid,context)           
        pricelist = order.pricelist_id
        curText = ""
        if pricelist and pricelist.currency_id:
            curText = pricelist.currency_id.symbol
        
        res["order"] = order.name
        res["total"] = lf_pos.formatLang(order.amount_total) +" "+ curText
        resLines = []
        res["lines"] = resLines
        for line in order.lines:            
            str_discount = ""
            if line.discount:
                str_discount = "-" + str(line.discount) + '%'
            
            product = line.product_id            
            uom = product.uom_id                        
            resLine = { "id" : line.id,
                        "name" :  product.name, 
                        "price" : lf_pos.formatLang(line.price_brutto) + " " + curText, 
                        "total" : lf_pos.formatLang(line.subtotal_brutto) + " " + curText,
                        "qty" :  lf_uom.formatLang(line.qty),
                        "disc" : str_discount,
                        "uom" : uom and uom.name or None 
                      }
                        
            resLines.append(resLine)             
            
        if empty_product_id:
            product_obj = self.pool.get("product.product")
            product = product_obj.browse(cr, uid, empty_product_id, context)
            uom = product.uom_id 
            resLine = { "id" : 0,
                        "name" :  product.name, 
                        "price" : lf_pos.formatLang(0.0) + " " + curText, 
                        "total" : lf_pos.formatLang(0.0) + " " + curText,
                        "qty" :  lf_uom.formatLang(0.0),
                        "disc" : "",
                        "uom" : uom and uom.name or None 
                      }                                    
            resLines.append(resLine)        
            
        return res
        
    def pos_overall_discount(self,cr,uid,order,discount,context=None):
        if self._lock_order_lines(cr, uid, order):
            line_obj = self.pool.get("pos.order.line")
            ids = line_obj.search(cr, uid, [('order_id','=',order)])
            if ids:
                if discount >= 0:                               
                    line_obj.write(cr, uid, ids, {"discount" : discount }, context)                
                else:
                    values = line_obj.read(cr, uid, ids, ["discount"], context)
                    for value in values:
                        read_discount = value.get("discount",0.0)
                        read_discount += discount
                        if read_discount < 0.0:
                            read_discount = 0.0
                        line_obj.write(cr, uid, value["id"], {"discount" : read_discount }, context)                    
            
        return self.pos_order_view(cr,uid,order,context)
            
            
    def pos_modify_line(self, cr, uid, product_id, qty, discount, order,context=None):
        if self._lock_order_lines(cr, uid, order):
            line_obj = self.pool.get("pos.order.line")
            line_obj.pos_modify_line(cr, uid, product_id, qty, discount, order)
        
        return self.pos_order_view(cr,uid,order,context)
                       
    def pos_do_scan(self,cr,uid,ean,order,context):        
        product_obj = self.pool.get("product.product")
        if len(ean)==12: #correct wrong size
            ean = "0%s" % (ean,)            
        ids = product_obj.search(cr, uid, [("ean13","=",ean)], limit=1)
        if ids:
            line_obj = self.pool.get("pos.order.line")
            product = product_obj.browse(cr, uid, ids[0], context)
                        
            if product.needs_measure:
                res = self.pos_order_view(cr,uid,order,context,empty_product_id=product.id)                
                res["inputNeeded"] = {
                    "index" : len(res["lines"])-1,
                    "id" : product.id,
                    "name" : product.name,
                    "needs_measure" : True
                }                
            else:
                line_obj.pos_modify_line(cr,uid,product.id,1.0,0.0,order)
                res = self.pos_order_view(cr,uid,order,context)
                
            res["product_id"] = product.id
            return res
            
        else:
            return ean
        
    def create_account_move(self, cr, uid, ids, context=None):
        """Create a account move line of order  """
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        account_period_obj = self.pool.get('account.period')
        account_tax_obj = self.pool.get('account.tax')
        res_obj=self.pool.get('res.users')
        property_obj=self.pool.get('ir.property')
        period = account_period_obj.find(cr, uid, context=context)[0]

        for order in self.browse(cr, uid, ids, context=context):
            curr_c = res_obj.browse(cr, uid, uid).company_id
            comp_id = res_obj.browse(cr, order.user_id.id, order.user_id.id).company_id
            comp_id = comp_id and comp_id.id or False
            to_reconcile = []
            group_tax = {}
            account_def = property_obj.get(cr, uid, 'property_account_receivable', 'res.partner', context=context).id

            order_account = order.partner_id and order.partner_id.property_account_receivable and order.partner_id.property_account_receivable.id or account_def or curr_c.account_receivable.id

            # Create an entry for the sale
            move_id = account_move_obj.create(cr, uid, {
                'name' : order.name,
                'journal_id': order.sale_journal.id,
                'period_id': period,
                }, context=context)

            # Create an move for each order line
            total_brutto = 0.0                        
            for line in order.lines:   
                computed = account_tax_obj.compute_all(
                        cr, uid,  line.product_id.taxes_id, line.price_unit, line.qty)
                
                computed_taxes = computed["taxes"]
                
                #
                line_netto = computed["total"]
                line_brutto = computed["total_included"]
                total_brutto += line_brutto
                base_tax_code_id = False
                tax_amount = 0.0
                #           
                for tax in computed_taxes:                    
                    group_key = (tax["tax_code_id"],
                                tax["base_code_id"],
                                tax["account_collected_id"])
                    #
                    tax_amount = group_tax.get(group_key,0.0)
                    tax_amount += tax["amount"]
                    group_tax[group_key]=tax_amount
                    #
                    if not base_tax_code_id:
                        if line_netto > 0.0:
                            base_tax_code_id = tax["base_code_id"]
                            tax_amount = line_netto * tax["base_sign"]
                        else:
                            base_tax_code_id = tax["base_code_id"]
                            tax_amount = line_netto * tax["ref_base_sign"]
                        
                
                # Search for the income account
                if  line.product_id.property_account_income.id:
                    income_account = line.\
                                    product_id.property_account_income.id
                elif line.product_id.categ_id.\
                        property_account_income_categ.id:
                    income_account = line.product_id.categ_id.\
                                    property_account_income_categ.id
                else:
                    raise osv.except_osv(_('Error !'), _('There is no income '\
                        'account defined for this product: "%s" (id:%d)') \
                        % (line.product_id.name, line.product_id.id, ))

               
                # Create a move for the line
                # z.B. 4000 Erloese aa
                account_move_line_obj.create(cr, uid, {
                    'name': order.name,
                    'date': order.date_order[:10],
                    'ref': order.contract_number or order.name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'move_id': move_id,
                    'account_id': income_account,
                    'company_id': comp_id,
                    'credit': ((line_netto>0) and line_netto) or 0.0,
                    'debit': ((line_netto<0) and -line_netto) or 0.0,
                    'journal_id': order.sale_journal.id,
                    'period_id': period,
                    'tax_code_id': base_tax_code_id,
                    'tax_amount': tax_amount,
                    'partner_id': order.partner_id and order.partner_id.id or False
                }, context=context)
              

            # Create a move for each tax group
            # UST Grouped by UST Type
            (tax_code_pos, base_code_pos, account_pos) = (0, 1, 2)
            for key, amount in group_tax.items():
                account_move_line_obj.create(cr, uid, {
                    'name': order.name,
                    'date': order.date_order[:10],
                    'ref': order.contract_number or order.name,
                    'move_id': move_id,
                    'company_id': comp_id,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': key[account_pos],
                    'credit': ((amount>0) and amount) or 0.0,
                    'debit': ((amount<0) and -amount) or 0.0,
                    'journal_id': order.sale_journal.id,
                    'period_id': period,
                    'tax_code_id': key[tax_code_pos],
                    'tax_amount': amount,
                }, context=context)

            # counterpart
            # z.B. Debitor Account -> The full Amount inkl. Ust
            to_reconcile.append(account_move_line_obj.create(cr, uid, {
                'name': order.name,
                'date': order.date_order[:10],
                'ref': order.contract_number or order.name,
                'move_id': move_id,
                'company_id': comp_id,
                'account_id': order_account,
                'credit': ((total_brutto < 0) and -total_brutto)\
                    or 0.0,
                'debit': ((total_brutto > 0) and total_brutto)\
                    or 0.0,
                'journal_id': order.sale_journal.id,
                'period_id': period,
                'partner_id': order.partner_id and order.partner_id.id or False
            }, context=context))


            # search the account receivable for the payments:
            account_receivable = order.sale_journal.default_credit_account_id.id
            if not account_receivable:
                raise  osv.except_osv(_('Error !'),
                    _('There is no receivable account defined for this journal:'\
                    ' "%s" (id:%d)') % (order.sale_journal.name, order.sale_journal.id, ))
          
            # handle is is_acc
            # i dont know for what it is            
            for stat_l in order.statement_ids:
                if stat_l.is_acc and len(stat_l.move_ids):
                    for st in stat_l.move_ids:
                        for s in st.line_id:
                            if s.credit:
                                account_move_line_obj.copy(cr, uid, s.id, {
                                                        'debit': s.credit,
                                                        'statement_id': False,
                                                        'credit': s.debit
                                                    })
                                account_move_line_obj.copy(cr, uid, s.id, {
                                                        'statement_id': False,
                                                        'account_id': order_account
                                                     })
                                
            account_move_obj.post(cr,uid,[move_id],context=context)
            self.write(cr, uid, order.id, {'state':'done'}, context=context)
        return True
        
pos_order()
