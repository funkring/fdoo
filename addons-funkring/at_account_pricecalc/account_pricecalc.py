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

from openerp.osv import fields,osv
import decimal_precision as dp

class pricecalc_wizard(osv.osv_memory):
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(pricecalc_wizard,self).default_get(cr,uid,fields_list,context)
        if context:
            active_model = context.get("active_model")
            active_ids = context.get("active_ids")
            if active_ids and active_model=="account.invoice.line":
                line_obj = self.pool.get("account.invoice.line")
                line = line_obj.browse(cr,uid,active_ids[0],context)
                purchase_price = line_obj._purchase_price(cr,uid,line.id,context)
                if purchase_price:
                    res["purchase_price"]=purchase_price["price"]       
                    purchase_line = line_obj.browse(cr,uid,purchase_price["invoice_line_id"],context)             
                    res["purchase_invoice_line_id"]=(purchase_line.invoice_id.state == "draft" and purchase_line.id) or False
                
                description = line.name
                if line.note:
                    description = description + "\n\n" + line.note                
                res["description"]=description
                res["sale_invoice_line_id"]=(line.invoice_id.state == "draft" and line.id) or False
                res["sales_price"]=line.price_unit                
        return res
    
    def on_change_price(self, cr, uid, ids, purchase_price, marge_percent, sales_price):
        if purchase_price and sales_price and marge_percent:
            if marge_percent != 100.0:
                sales_price = 0
            else:
                marge_percent = 0.0
                                
        value = {}
        res = {"value" : value}        
        expense_percent = 100.0-marge_percent     
        if not sales_price and marge_percent and purchase_price and expense_percent:         
            sales_price = (purchase_price / expense_percent) * 100.0
            value["sales_price"] = sales_price
        elif not marge_percent and sales_price:           
            marge_percent=100.0-((100.0 / sales_price)*purchase_price)
            value["marge_percent"] = marge_percent
        elif not purchase_price and marge_percent and sales_price:
            purchase_price = (sales_price / 100.0) * (100-marge_percent)
            value["purchase_price"] = purchase_price
        
        value["marge"]=sales_price - purchase_price        
        return res
    
    def on_change_marge(self, cr, uid, ids, purchase_price, marge, sales_price):
        sales_price = purchase_price+marge
        res =  self.on_change_price(cr,uid,ids,purchase_price,False,sales_price)       
        res["value"]["sales_price"]=sales_price
        return res 
    
    def change_price(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            inv_line_obj = self.pool.get("account.invoice.line")                        
            if obj.purchase_invoice_line_id \
                    and obj.purchase_invoice_line_id.invoice_id.state == "draft" \
                    and obj.purchase_invoice_line_id.price_unit != obj.purchase_price:                
                inv_line_obj.write(cr,uid,[obj.purchase_invoice_line_id.id], {"price_unit" : obj.purchase_price })
            
            if obj.sale_invoice_line_id \
                    and obj.sale_invoice_line_id.invoice_id.state == "draft" \
                    and obj.sale_invoice_line_id.price_unit != obj.sales_price:
                inv_line_obj.write(cr,uid,[obj.sale_invoice_line_id.id], {"price_unit" : obj.sales_price })
        return { "type" : "ir.actions.act_window_close" }              
                
           
    _columns = {     
        "description" : fields.text("Description",readonly=True),
        "purchase_invoice_line_id" : fields.many2one("account.invoice.line","Invoice Line"),
        "sale_invoice_line_id" : fields.many2one("account.invoice.line","Invoice Line"),        
        "purchase_price" : fields.float("Purchase Price",digits_compute=dp.get_precision("Purchase Price")),
        "marge" : fields.float("Marge",digits_compute=dp.get_precision("Purchase Price")),
        "marge_percent" : fields.float("Marge %"),
        "sales_price" : fields.float("Sale Price",digits_compute=dp.get_precision("Sale Price"))
      
    }
    _name = "at_account_pricecalc.pricecalc_wizard"
    _description="Pricecalculation Wizard"
pricecalc_wizard()