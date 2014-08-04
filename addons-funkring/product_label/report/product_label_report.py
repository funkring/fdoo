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

from openerp.report import report_sxw
from openerp.osv import orm

class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "lines" : self.lines,
            "label" : self.label
        })        
                
        self.company = self.pool.get("res.users").browse(cr,uid,uid).company_id        
        self.currency = (self.company and self.company.currency_id and self.company.currency_id.symbol) or ""
        if self.company:
            self.localcontext["force_company"]=self.company.id               
        self.pricelist = self.pool.get("ir.property").get(cr,uid,"property_product_pricelist","res.partner",context=self.localcontext)
        self.pricelist_obj = self.pool.get("product.pricelist")
        
    def lines(self):        
        plines = []
        pcols = []
        plines.append(pcols)                
        for o in self.objects:
            if len(pcols) >= 4:
                pcols = []
                plines.append(pcols)
            pcols.append(o)        
        return plines

    def label(self,line,index):
        value = {
          "title" : "",
          "text" : "",         
          "price" : ""
        }
        if index < len(line):
            product = line[index]
            value["product"]=product
            text = None
            
            if product.description_sale:
                lines=product.description_sale.split("\n")
                value["title"]=lines[0]
                if len(lines) > 1:
                    text = lines[1:3]       
            else:
                text = []
                if product.categ_id:                
                    category_names = product.categ_id.complete_name.split(" / ")                 
                    value["title"]=category_names[0]      
                text.append(product.name)                
            if text:
                value["text"]=self.format("\n".join(text))
          
            price = 0.0
            if self.pricelist:          
                #(self, cr, uid, ids, prod_id, qty, partner=None, context=None):                     
                price = self.pricelist_obj.price_get(self.cr,self.uid,[self.pricelist.id],product.id,1.0)[self.pricelist.id]
            else:
                price=product.list_price
                
            value["price"]=self.formatLang(price) + " " + self.currency
        else:
            value["product"] = orm.browse_null()
        return value        
         



