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
            "sale_layout": self._sale_layout,
            "currency" : self._currency,
            "payment_term" : self._payment_term,
            "taxes" : self._taxes,
            "invoice_text" : self._invoice_text
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

    
    def _sale_layout(self, invoice):
        invoice_obj = self.pool.get("account.invoice")
        res = invoice_obj.sale_layout_lines(self.cr, self.uid, [invoice.id], invoice_id=invoice.id, context=self.localcontext)

        categ_pos = 1
        product_categ_pos = 1      
        pos = 1
         
        for categ in res:
            prepared_lines = []      
            product_categ_list = []
            product_categ_dict = {} 
            categ["pos"] = "{:02d}".format(categ_pos)     
            lines = categ.get("lines")
            if lines:
                for line in lines:
                    
                    # check category
                    product_categ = line.product_id and line.product_id.categ_id or None
                    product_categ_name = product_categ and product_categ.name or ''
                    product_categ_values = product_categ_dict.get(product_categ_name, None)
                    if product_categ_values is None:
                        pos = 1
                        product_categ_values = { "prod_categ" : product_categ, 
                                                 "sequence" : product_categ_pos,
                                                 "lines" : [], 
                                                 "pos":"{:02d}.{:02d}".format(categ_pos, product_categ_pos)}
                        product_categ_dict[product_categ_name] = product_categ_values
                        product_categ_list.append(product_categ_values)
                        product_categ_pos += 1
                    
                    # line name
                    notes = []
                    lines = line.name.split("\n")
                    line_name = lines and lines[0] or ""
                    if len(lines) > 1:
                        notes.extend(lines[1:])
                    
                    # line notes
                    #if line.note:
                    #    notes.extend(line.note.split("\n"))
                    line_note = "\n".join(notes)
                    
                    line_res = {}
                    line_res['tax_id'] = ', '.join(map(lambda x: x.name, line.invoice_line_tax_id)) or ''
                    line_res['name'] = line_name
                    line_res["note"] = line_note
                    line_res['product_uom_qty'] = line.quantity or 0.00
                    line_res['product_uom'] = line.uos_id and line.uos_id.name or ''
                    line_res['price_unit'] = line.price_unit or 0.00
                    line_res['discount'] = line.discount or 0.00
                    line_res['price_subtotal'] = line.price_subtotal or 0.00 
                    line_res['price_subtotal_taxed'] = line.price_subtotal_taxed or 0.00
                    line_res['currency'] = self._currency(invoice)
                    line_res['pos'] = "{:02d}.{:02d}.{:03d}".format(categ_pos, product_categ_values["sequence"], pos)
                    line_res['id'] = line.id
                    line_res['line'] = line
                    
                    # increment pos
                    pos += 1
                    prepared_lines.append(line_res)
                    # add lines
                    product_categ_values["lines"].append(line_res)
                
                categ["lines"] = prepared_lines
                categ["product_categ"] = product_categ_list
            
            categ_pos += 1
        
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

