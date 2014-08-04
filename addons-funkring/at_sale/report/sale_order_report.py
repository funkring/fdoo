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
            "sale_order_lines": self.sale_order_lines,            
            "currency" : self.currency,
            "payment_note" : self.payment_note,
            "payment_term" : self.payment_term,
            "taxes" : self.taxes
        })
       
    def payment_note(self,sale_order):
        return format(sale_order.payment_term and sale_order.payment_term.note or '')
    
    def currency(self,sale_order):
        return (sale_order.pricelist_id and sale_order.pricelist_id.currency_id and sale_order.pricelist_id.currency_id.symbol) or ''
    
    def payment_term(self,sale_order):
        return self.payment_note(sale_order)
    
    def taxes(self,sale_order):
        t_res = {}
        t_tax_obj = self.pool.get("account.tax")
        t_sale_obj = self.pool.get("sale.order")
        for t_tax_id, t_tax_amount in t_sale_obj._tax_amount(self.cr,self.uid,sale_order.id,self.localcontext).items():
            t_tax = t_tax_obj.browse(self.cr,self.uid,t_tax_id,self.localcontext)
            t_amount = t_res.get(t_tax.name,0.0)
            t_amount += t_tax_amount
            t_res[t_tax.name] = t_amount

        return t_res
       
    def prepare(self, sale_order):
        prepared_lines = []
        order_lines = []      
        obj_order_line = self.pool.get('sale.order.line')
        ids = obj_order_line.search(self.cr, self.uid, [('order_id', '=', sale_order.id)])
        for sid in range(0, len(ids)):
            order = obj_order_line.browse(self.cr, self.uid, ids[sid], self.localcontext)
            order_lines.append(order)
            
        pos = 1            
        for line in order_lines:
            
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
            
            res = {}
            res['tax_id'] = ', '.join(map(lambda x: x.name, line.tax_id)) or ''
            res['name'] = line_name
            res["note"] = line_note
            res['product_uom_qty'] = line.product_uos and line.product_uos_qty or line.product_uom_qty or 0.00
            res['product_uom'] = line.product_uos and line.product_uos.name or line.product_uom.name
            res['price_unit'] = line.price_unit or 0.00
            res['discount'] = line.discount or 0.00
            res['price_subtotal'] = line.price_subtotal or 0.00 
            res['price_subtotal_taxed'] = line.price_subtotal_taxed or 0.00
            res['currency'] = sale_order.pricelist_id.currency_id.symbol
            res['pos'] = str(pos)
            res['id'] = line.id
            pos += 1
            prepared_lines.append(res)
            
        res = [{                
          "lines" : prepared_lines,         
        }]
        return res
            
           
    def sale_order_lines(self, sale_order):
        return self.prepare(sale_order)[0]["lines"]                 
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

