# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.addons.at_base import extreport

class Parser(extreport.basic_parser):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "time": time,
            "invoice_lines": self._invoice_lines,            
            "currency" : self._currency,
            "payment_term" : self._payment_term,
            "taxes" : self._taxes,
            "invoice_text" : self._invoice_text,
        })
                    
    def _payment_term(self,invoice):
        return invoice.payment_term and invoice.payment_term.name or ''     
     
    def _currency(self,invoice):
        return invoice.currency_id.symbol or ""
  
    def _invoice_text(self,invoice):
        return invoice.invoice_text    
        
    def _taxes(self,invoice):
        t_res = {}
        t_tax_obj = self.pool.get("account.tax")
        t_invoice_obj = self.pool.get("account.invoice")
        for t_tax_id, t_tax_amount in t_invoice_obj._tax_amount(self.cr,self.uid,invoice.id,self.localcontext).items():
            t_tax = t_tax_obj.browse(self.cr,self.uid,t_tax_id,self.localcontext)
            t_amount = t_res.get(t_tax.name,0.0)
            t_amount += t_tax_amount
            t_res[t_tax.name] = t_amount

        return t_res
    
    def _invoice_lines(self, invoice):
        result = []
        invoice_lines = []      
        invoice_line_obj = self.pool.get("account.invoice.line")
        ids = invoice_line_obj.search(self.cr, self.uid, [('invoice_id', '=', invoice.id)])
        for i in range(0, len(ids)):
            lines = invoice_line_obj.browse(self.cr, self.uid, ids[i], self.localcontext)
            invoice_lines.append(lines)
            
        pos = 1
        for line in invoice_lines:
            res = {}
            notes = []
            
            # line name
            lines = line.name.split("\n")
            line_name = lines and lines[0] or ""
            if len(lines) > 1:
                notes.extend(lines[1:])
            
            # line notes
            if line.note:
                notes.extend(line.note.split("\n"))
            line_notes = "\n".join(notes)
                            
            res['tax_id'] = ', '.join(map(lambda x: x.name, line.invoice_line_tax_id)) or ''
            res['name'] = line_name
            res['product_uom_qty'] = line.quantity or 0.00
            res['product_uom'] = line.uos_id and line.uos_id.name or ''
            res['price_unit'] = line.price_unit or 0.00
            res['discount'] = line.discount or 0.00
            res['price_subtotal'] = line.price_subtotal or 0.00 
            res['price_subtotal_taxed'] = line.price_subtotal_taxed or 0.00                       
            res['note'] = (line_notes and format(line_notes)) or ''
            res['currency'] = self._currency(invoice)                        
            res['pos'] = pos
            res['discount_amount'] = line.discount_amount or 0.00
            res['invoice_line'] = line
            pos += 1                 
            result.append(res)
        return result           
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

