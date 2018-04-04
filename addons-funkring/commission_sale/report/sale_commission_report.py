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
        
        cr.execute("SELECT cl.id FROM commission_line cl "
                    " INNER JOIN commission_invoice_line_rel lr ON lr.commission_line_id = cl.id "
                    " INNER JOIN account_invoice_line il ON il.id = lr.invoice_line_id "                    
                    " WHERE il.invoice_id = %s "
                    " ORDER BY il.sequence ", (invoice.id,))
        
        line_ids = [r[0] for r in cr.fetchall()]
        lines = line_obj.browse(cr, uid, line_ids, context=context)
        
        sum_netto = 0
        sum_prov = 0
        avg_prov = 0
          
        cuLineDict = {}
        cuLineList = []
                
        for line in lines:
            sum_netto += line.price_sub
            sum_prov += (line.amount*-1.0)
            avg_prov += line.total_commission
            
            cuLines = cuLineDict.get(line.sale_partner_id.id, None)
            if cuLines is None:
              cuLines = []
              cuLineDict[line.sale_partner_id.id] = cuLines
              cuLineList.append((line.sale_partner_id, cuLines))
              
            cuLines.append(line)
            
        line_count = len(lines)
        if line_count:
            avg_prov = avg_prov / line_count
        
        prov = 0
        if sum_netto:
            prov = 100.0 / sum_netto * sum_prov
        
        return [{
            "currency" : self.localcontext["company"].currency_id,
            "lines" : lines,
            "cuLines": cuLineList,
            "sum_netto" : sum_netto,
            "avg_prov" : avg_prov,
            "prov" : prov,
            "sum_prov" : sum_prov
        }]
        
        
