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

class account_invoice(osv.osv):
                      
    def _order_ids(self, cr, uid, ids, field_name, args, context=None):
        
        res = dict.fromkeys(ids)
        
        for oid in ids:
            cr.execute("SELECT order_id FROM sale_order_invoice_rel WHERE invoice_id=%s",(oid,))       
            order_ids = []
            for row in cr.fetchall():
                order_id = row[0]
                if order_id:
                    order_ids.append(order_id)
            res[oid]=order_ids
            
        return res
        
    def _shop_ids(self, cr, uid, ids, field_name, args, context=None):
        
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids):
            shop_ids = []
            for order in obj.order_ids:
                shop_ids.append(order.shop_id.id)
            res[obj.id] = shop_ids
                
        
        return res
    #Amplify the invoice_text method from at_account, which adds the text from the shop_ids
    #if there are more than 1 shop, concatenate all texts from the shops, which are split up by an Enter
    def _invoice_text(self, cr, uid, ids, field_name, args, context=None):    
        
        res = super(account_invoice, self)._invoice_text(cr, uid, ids, field_name, args, context)
        
        for invoice in self.browse(cr, uid, ids):
            invoice_text_lines = []
            for shop in invoice.shop_ids:
                if invoice.type == "out_invoice":
                    invoice_text = shop.invoice_text                    
                elif invoice.type == "in_invoice":
                    invoice_text = shop.invoice_in_text                    
                elif invoice.type == "out_refund":
                    invoice_text = shop.refund_text                    
                elif invoice.type ==  "in_refund":
                    invoice_text = shop.refund_in_text
                
                if invoice_text:
                    invoice_text_lines.append(invoice_text)
                    
            if invoice_text_lines:
                res[invoice.id]="\n".join(invoice_text_lines)
                
        return res
        
        
    _inherit = "account.invoice"
    _columns = {
        "order_ids" : fields.function(_order_ids, type="many2many", obj="sale.order", string="Sale Orders", readonly=True),
        "shop_ids" : fields.function(_shop_ids, type="many2many", obj="sale.shop", string="Shops", readonly=True),
        "invoice_text" : fields.function(_invoice_text, type="text", string="Invoice Text")
    }
account_invoice()