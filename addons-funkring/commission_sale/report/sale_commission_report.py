from openerp.addons.at_base import extreport

class Parser(extreport.basic_parser):

    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "commission": self._commission
        })
        
    def _commission(self, invoice):
        cr = self.cr
        context = self.localcontext
        uid = self.uid
        
        line_obj = self.pool["commission.line"]
        line_ids = line_obj.search(cr, uid, [("invoiced_id","=",invoice.id)], context=context)
        lines = line_obj.browse(cr, uid, line_ids, context=context)
        
        sum_netto = 0
        sum_prov = 0
        avg_prov = 0
                
        for line in lines:
            sum_netto += line.price_sub
            sum_prov += (line.amount*-1.0)
            avg_prov += line.total_commission
            
        line_count = len(lines)
        if line_count:
            avg_prov = avg_prov / line_count
        
        prov = 0
        if sum_netto:
            prov = 100.0 / sum_netto * sum_prov
        
        return [{
            "currency" : self.localcontext["company"].currency_id,
            "lines" : lines,
            "sum_netto" : sum_netto,
            "avg_prov" : avg_prov,
            "prov" : prov,
            "sum_prov" : sum_prov
        }]
        
        
