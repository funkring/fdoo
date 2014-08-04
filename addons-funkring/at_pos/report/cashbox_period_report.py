'''
Created on 17.05.2011

@author: martin
'''
from openerp.report import report_sxw
from openerp.tools.translate import _
from at_base import util

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({            
            "statistic": self.statistic,
            "currency" : self.currency,
            "journal" : self.journal,
            "statements" : self.statements
        })
                
        self.context = context                
        res_users_obj = self.pool.get('res.users')
        self.company_currency = res_users_obj.browse(cr, uid, uid,context=context).company_id.currency_id.symbol        
     
    def _statement_ids(self,period):
        statement_obj = self.pool.get("account.bank.statement")        
        search = [("period_id","=",period.id),("state","=","confirm")]
        journal_id = self.context.get("journal_id")
        if journal_id:
            search.append(("journal_id","=",journal_id))
        else:
            search.append(("parent_id","=",None))
        return statement_obj.search(self.cr,self.uid,search)    
         
    def statements(self,period):
        statement_obj = self.pool.get("account.bank.statement")        
        return  statement_obj.browse(self.cr,self.uid,self._statement_ids(period),context=self.context)
         
    def currency(self,period):
        return self.company_currency
      
    def journal(self):        
        journal_id = self.context.get("journal_id")
        if journal_id:
            journal_obj = self.pool.get("account.journal")
            return journal_obj.browse(self.cr,self.uid,journal_id).name
        return None
        
    def append_tax_stat(self,tax_stats,tax_stat):
        tName = tax_stat["name"]
        for cur_stat in tax_stats:            
            if tName == cur_stat["name"]:
                cur_stat["sum"] = cur_stat["sum"]+tax_stat["sum"]
                cur_detail = cur_stat["detail"]
                cur_detail += tax_stat["detail"]                
                return                                    
        tax_stats.append(tax_stat)
                       
    def statistic(self,period):        
        stat_per_tax = {}
        stat_per_product = {}
                
        payin = 0.0
        payout = 0.0
        difference = 0.0
               
        account_tax_obj = self.pool.get("account.tax")
        currency_obj = self.pool.get("res.currency")
        statement_obj = self.pool.get("account.bank.statement")
        journal_obj = self.pool.get("account.journal")
        partner_obj = self.pool.get("res.partner")
        account_obj = self.pool.get("account.account")
        
        search = [("period_id","=",period.id)]
        journal_id = self.context.get("journal_id")
        if journal_id:
            search.append(("journal_id","=",journal_id))
        else:
            search.append(("parent_id","=",None))
            
        stat_dict = {}
        used_statement_ids = []    
        #        
        for statement in statement_obj.browse(self.cr,self.uid,self._statement_ids(period)):   
            difference+=statement.balance_end_cash-statement.balance_end
            used_statement_ids.append(statement.id)
            #            
            child_ids = statement_obj.search(self.cr,self.uid,[("parent_id","=",statement.id),("state","=","confirm")])
            child_ids.append(statement.id)            
            #
            for child in statement_obj.browse(self.cr,self.uid,child_ids):
                used_statement_ids.append(child.id)
                child_journal = child.journal_id
                child_stat = stat_dict.get(child_journal.id)
                debit_sum = 0.0
                credit_sum = 0.0
                for line in child.line_ids:
                    amount = line.amount
                    debit = amount >= 0.0 and amount or 0.0
                    credit = amount < 0.0 and amount or 0.0
                    debit_sum+=debit
                    credit_sum+=credit
                    
                if not child_stat:                        
                    child_stat = {
                        "journal" : child_journal,
                        "debit" : debit_sum,
                        "credit" : credit_sum
                    }
                    stat_dict[child_journal.id]=child_stat
                else:
                    child_stat["debit"]=child_stat["debit"]+debit_sum
                    child_stat["credit"]=child_stat["credit"]+credit_sum
                #
                if journal_id == None or journal_id == child_journal.id:
                    payin += debit_sum
                    payout += credit_sum
                #
            for line in statement.pos_paid_order_line_ids:
                product = line.product_id
                
                taxes = [x for x in line.product_id.taxes_id]
                if line.qty == 0.0:            
                    continue
                            
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                computed_taxes = account_tax_obj.compute_all(self.cr, self.uid, taxes, price, line.qty)
                cur = line.order_id.pricelist_id.currency_id                       
                total_inc = currency_obj.round(self.cr, self.uid, cur, computed_taxes['total_included'])
                #                
                payment_type = "in" #revenue
                if total_inc < 0:
                    payment_type = "out"
                                        
                def add_tax_stat(tax_id,tax_name):          
                        tax_stat = stat_per_tax.get(tax_id)
                        if not tax_stat:
                            tax_stat = { 
                                "name" : tax_name,
                                "in" : { "detail" : [], "sum" : 0.0 }, 
                                "out"  : { "detail" : [], "sum" : 0.0 } }                    
                            stat_per_tax[tax_id] = tax_stat
                        
                        payment_stat = tax_stat.get(payment_type)                
                        tax_sum = payment_stat.get("sum", 0.0)
                        tax_sum += total_inc
                        payment_stat["sum"]=tax_sum
                        
                        #should shown as detail
                        if product.is_detail_product:####### product_product
                            detail = payment_stat.get("detail")                                                              
                            detail.append( { "name" : product.name, "total" : total_inc })
                            
                #add to taxes
                if product.expense_pdt or product.income_pdt:
                    product_stat = stat_per_product.get(product.id)
                    if not product_stat:
                        product_stat = {
                            "name" : product.name,
                            "sum" : 0.0
                        }
                        stat_per_product[product.id]=product_stat
                    product_stat["sum"]= product_stat["sum"]+total_inc
                elif taxes:            
                    for tax in taxes:
                        add_tax_stat(tax.id,tax.name)                  
                else:
                    add_tax_stat(0,_("w/o tax"))
                    tax_stat = stat_per_tax.get(0)
                       
        #get journal sub stats ordered            
        journals = []
        journal_ids = journal_obj.search(self.cr,self.uid,[])
        for journal_id in journal_ids:
            statement_stat = stat_dict.get(journal_id)
            if statement_stat:
                journals.append(statement_stat)
              
        self.cr.execute("SELECT l.partner_id, p.name from account_bank_statement_line l "  
                        " INNER JOIN res_partner p ON p.id = l.partner_id " 
                        " WHERE l.statement_id IN %s "
                        " GROUP BY 1,2 ORDER BY p.name ", (tuple(used_statement_ids),))
        
        used_partner_ids = [r[0] for r in self.cr.fetchall()]
        partners = []
        for partner in partner_obj.browse(self.cr,self.uid,used_partner_ids,context=self.context):
            account_debit = partner.property_account_receivable
            day_before = util.datePrivious(period.date_start)
            day_end = period.date_stop                
            #
            balance_before = account_obj._compute_account(self.cr,self.uid,[account_debit.id],date_till=day_before,context=self.context)[account_debit.id]["balance"]
            balance = account_obj._compute_account(self.cr,self.uid,[account_debit.id],date_till=day_end,context=self.context)[account_debit.id]["balance"]
            #
            partner_name = []
            if account_debit.code:
                partner_name.append(account_debit.code)
            partner_name.append(partner.name)
            
            partners.append({
              "name" : " / ".join(partner_name),
              "balance_before" : balance_before and -balance_before or 0.0,
              "balance" : balance and -balance or 0.0               
            }) 
                                   
        stat = {
            "difference" : difference,
            "payin"  : payin,
            "payout" : payout,
            "journals" : journals,
            "partners" : partners,
            "product_statistic" : [product_stat]#.values()   
        }        
        
        tax_stats = []
        stat["tax_statistic"] = tax_stats
            
        if stat_per_tax:    
            for tax_id in stat_per_tax.keys():
                tax_stat = stat_per_tax[tax_id]                    
                tax_stat_in=tax_stat["in"]
                self.append_tax_stat(tax_stats, {
                     "name" : _("Receipts (%s)") % (tax_stat["name"],),
                     "sum" : tax_stat_in["sum"],
                     "detail" : tax_stat_in["detail"]
                })
                

                tax_stat_out=tax_stat["out"]
                self.append_tax_stat(tax_stats, {
                     "name" : _("Credits (%s)") % (tax_stat["name"],),
                     "sum" : tax_stat_out["sum"],
                     "detail" : tax_stat_out["detail"]
                })                
                
        return stat
            
  
       
   
