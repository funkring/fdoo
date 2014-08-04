'''
Created on 17.05.2011

@author: martin
'''
import time

from openerp.report import report_sxw
#from openerp.tools.translate import _

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,           
            'lines': self.lines,            
            'currency' : self.currency,            
            'taxes' : self.taxes,
            'amount_netto' : self.amount_netto
        })
        self.context = context
         
    def currency(self,order):
        return order.company_id.currency_id.symbol or ''
  
    def taxes(self,order):
        res = {}
        tax_obj = self.pool.get("account.tax")
        order_obj = self.pool.get("pos.order")
        for tax_id, tax_amount in order_obj._tax_amount(self.cr,self.uid,order.id,self.context).items():
            tax = tax_obj.browse(self.cr,self.uid,tax_id,self.context)
            t_amount = res.get(tax.name,0.0)
            t_amount += tax_amount
            res[tax.name] = t_amount            
        return res
    
    def amount_netto(self,order):
        return order.amount_total-order.amount_tax
    
    def lines(self, order):        
        result = []
        currency = self.currency(order)
                
        for line in order.lines:
            res = {}            
            product = line.product_id
            uom = product.uom_id or None
            
            res['name'] = product.name or ''
            res['product_uom_qty'] = line.qty or 0.00
            res['product_uom'] = uom and uom.name or ''            
            res['discount'] = line.discount or 0.00
            res['price_subtotal'] = line.subtotal_brutto or 0.00             
            res['currency'] = currency                             
            result.append(res)            
            
        return result           
   
   
