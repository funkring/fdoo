'''
Created on 17.05.2011

@author: martin
'''
from openerp.report import report_sxw
from openerp.tools.translate import _


class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "description" : self.description,
            "statistic": self.statistic,
            "currency" : self.currency,
            "stateText" : self.stateText,
            "payment_per_journal" : self.payment_per_journal,
            "get_income_payment_sum" : self.get_income_payment_sum,
            "get_journal_sum" : self.get_journal_sum
        })
        
        self.context = context
        
        res_users_obj = self.pool.get('res.users')
        self.company_currency = res_users_obj.browse(cr, uid, uid,context=context).company_id.currency_id.symbol                
        
         
    def currency(self,statement):
        return self.company_currency
                 
    def description(self,statement):
        res = ""        
        if statement.opening_date:
            res = self.formatLang(statement.opening_date, date_time=True)
        elif statement.date:
            res = self.formatLang(statement.date, date=True)                        
        if statement.closing_date:
            res += " - "
            res += self.formatLang(statement.closing_date, date_time=True)
        return res
        
    def stateText(self,statement):
        if statement.state  == "confirm":
            return _("Closed")
        else:
            return _("Unclosed")
        
    def payment_per_journal(self,statement):
        statement_ids = [statement.id]
        statement_obj = self.pool.get("account.bank.statement") 
        journal_obj = self.pool.get("account.journal")
        partner_obj = self.pool.get("res.partner")
        order_obj = self.pool.get("pos.order")
        
        for child in statement.child_ids:
            statement_ids.append(child.id)
        
        self.cr.execute("SELECT s.journal_id, p.name, p.balance, l.amount, pa.id, o.id FROM account_bank_statement_line l " 
                   " INNER JOIN account_bank_statement s ON s.id = l.statement_id AND s.id IN %s "
                   " INNER JOIN pos_order o ON o.id = l.pos_statement_id "
                   " LEFT JOIN res_partner pa ON pa.id = o.partner_id "
                   " LEFT JOIN pos_order_payment p ON p.statement_line_id = l.id ", (tuple(statement_ids),) ) 

        #build detail
        journal_stats = {}
        for journal_id, payment_name, balance, amount, partner_id, order_id in self.cr.fetchall():
            journal_stat = journal_stats.get(journal_id)
            if not journal_stat:
                journal = journal_obj.browse(self.cr,self.uid,journal_id,self.context)
                journal_stat = {
                    "balance_credit" : journal.balance_credit, 
                    "id" : journal_id,
                    "debit" : 0.0,
                    "credit" : 0.0,
                    "detail" : []
                }
                journal_stats[journal_id]=journal_stat
                
            if amount >= 0.0:
                journal_stat["debit"] = journal_stat["debit"]+amount
            else:
                journal_stat["credit"] = journal_stat["credit"]+amount
                        
            name = []            
            if partner_id and journal_stat["balance_credit"]:                                
                partner = partner_obj.browse(self.cr,self.uid,partner_id,context=self.context)
                partner_account = partner.property_account_receivable
                name.append(partner_account.code)                
                name.append(partner.name)
            
            if payment_name:
                name.append(_("Number: %s") % (payment_name,))
                if balance:
                    currency = self.currency(statement)
                    name.append(_("Balance: %s %s") % (self.formatLang(balance), currency))
                    name.append(_("New Balance %s %s") % (self.formatLang(balance-amount), currency)) 
              
            if name:                     
                order = order_obj.browse(self.cr,self.uid,order_id,context=self.context)
                name.insert(0, order.name)
                     
                journal_stat["detail"].append({
                  "name" : " / ".join(name),
                  "amount" : amount
                })
        
        #keep sorting
        res = []
        for statement in statement_obj.browse(self.cr,self.uid,statement_ids):
            journal_stat = journal_stats.get(statement.journal_id.id)
            if journal_stat:
                journal_stat["name"]=statement.name
                journal_stat["journal_name"]=statement.journal_id.name
                res.append(journal_stat)
        return res    
            
        
         
    def append_tax_stat(self,tax_stats,tax_stat):
        tName = tax_stat["name"]
        for cur_stat in tax_stats:            
            if tName == cur_stat["name"]:
                cur_stat["sum"] = cur_stat["sum"]+tax_stat["sum"]
                cur_detail = cur_stat["detail"]
                cur_detail += tax_stat["detail"]                
                return                                    
        tax_stats.append(tax_stat)
    
    
    def get_income_payment_sum(self, statement):
        res = {
            "income" : 0.0,
            "payment" : 0.0
        }
        
        for line in statement.line_ids:
            if line.amount < 0.0:
                res["payment"] = res["payment"] + line.amount
            elif line.amount > 0.0:
                res["income"] = res["income"] + line.amount
                
        return res
    
    
    def get_journal_sum(self, statement):
        sum = 0.0
        
        for line in statement.line_ids:
            if line.amount < 0.0:
                sum += line.amount
            elif line.amount > 0.0:
                sum += line.amount
        for child in statement.child_ids:
            for line in child.line_ids:
                if line.amount < 0.0:
                    sum += line.amount
                elif line.amount > 0.0:
                    sum += line.amount
        return sum
    
            
    def statistic(self,statement):
        stat_per_tax = {}
        expense_dict = {}
        income_dict = {}
        
        
        turnover = 0.0
        refund_sum = 0.0
        income_sum = 0.0
            
        #line_obj = self.pool.get("pos.order.line")
        account_tax_obj = self.pool.get("account.tax")
        currency_obj = self.pool.get('res.currency')
                
        for line in statement.pos_paid_order_line_ids:
            product = line.product_id
            taxes = [x for x in line.product_id.taxes_id]
            if line.qty == 0.0:            
                continue
                        
            price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
            computed_taxes = account_tax_obj.compute_all(self.cr, self.uid, taxes, price, line.qty)
            cur = line.order_id.pricelist_id.currency_id                       
            total_inc = currency_obj.round(self.cr, self.uid, cur, computed_taxes['total_included'])
            
            if product.expense_pdt:
                expense = expense_dict.get(product.id)
                if not expense:                                        
                    expense = {
                        "name" : product.name,
                        "sum" : total_inc
                    }
                    expense_dict[product.id] = expense
                else:
                    expense["sum"] = expense["sum"]+total_inc
                
                
            
            if product.income_pdt:
                income = income_dict.get(product.id)
                if not income:
                    income = {
                        "name" : product.name,
                        "sum" : total_inc
                    }
                    income_dict[product.id] = income
                else:
                    income["sum"] = income["sum"]+total_inc
                
            payment_type = "in" #revenue
            if total_inc < 0:
                payment_type = "out"
                
            if product.income_pdt or product.expense_pdt:    #not taxes:#produkt einzahlung oder produkt auszahlung:
                turnover+=total_inc
            else:
                turnover+=total_inc        
                if total_inc > 0:
                    income_sum+=total_inc
                elif total_inc < 0:
                    refund_sum+=total_inc        
      
      
            def add_tax_stat(tax_id,tax_name):          
                tax_stat = stat_per_tax.get(tax_id)
                if not tax_stat:
                    tax_stat = { 
                        "name" : tax_name,
                        "in" : { "detail" : {}, "sum" : 0.0 }, 
                        "out"  : { "detail" : {}, "sum" : 0.0 } }                    
                    stat_per_tax[tax_id] = tax_stat
                
                payment_stat = tax_stat.get(payment_type)                
                tax_sum = payment_stat.get("sum", 0.0)
                tax_sum += total_inc
                payment_stat["sum"]=tax_sum
                
                #should shown as detail
                if product.is_detail_product:####### product_product
                    detail = payment_stat.get("detail")
                    detail_get = detail.get(product.id)
                    if detail_get:
                        detail_get["total"] = detail_get["total"] + total_inc
                    else:
                        detail_dict = {
                            "name" : product.name,
                            "total" : total_inc
                        }
                        detail[product.id] = detail_dict
                        
            #add to taxes
            if not product.income_pdt and not product.expense_pdt:
                if taxes:            
                    for tax in taxes:
                        add_tax_stat(tax.id,tax.name)                  
                else:
                    add_tax_stat(0,_("w/o tax"))
                    tax_stat = stat_per_tax.get(0)
                
        
        stat = {
            "turnover" : turnover            
        }        
                
                
        tax_stats = []
        stat["tax_statistic"] = tax_stats
        stat["expense"] = expense_dict.values()
        stat["income"] = income_dict.values()
        stat["refund_sum"] = refund_sum
        stat["income_sum"] = income_sum
            
        if stat_per_tax:    
            for tax_id in stat_per_tax.keys():
                tax_stat = stat_per_tax[tax_id]
                
                tax_stat_in=tax_stat["in"] #income
                self.append_tax_stat(tax_stats, {
                     "name" : _("Receipts (%s)") % (tax_stat["name"],),
                     "sum" : tax_stat_in["sum"],
                     "detail" : tax_stat_in["detail"].values()
                })
                

                tax_stat_out=tax_stat["out"] #refund
                self.append_tax_stat(tax_stats, {
                     "name" : _("Credits (%s)") % (tax_stat["name"],),
                     "sum" : tax_stat_out["sum"],
                     "detail" : tax_stat_out["detail"].values()
                })                
                
        return stat
            
    
        
       
   
