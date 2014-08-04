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
import time

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "time" : time,            
            "address_lines" : self._address_lines,
            "delivery_address_lines" : self._delivery_address_lines,
            "get_line_tax": self._get_line_tax,
            "get_tax": self._get_tax,
            "get_product_code": self._get_product_code,
        })

    def _address_lines(self,purchase):
        partner = purchase.partner_id or None
        if partner:
            partner_obj = self.pool.get("res.partner")
            return partner_obj._build_address_text(self.cr, self.uid, partner) 
        return []  
    
    def _delivery_address_lines(self,purchase):
        partner = purchase.dest_address_id or (purchase.warehouse_id and purchase.warehouse_id.partner_id) or None
        if partner:
            partner_obj = self.pool.get("res.partner")
            return partner_obj._build_address_text(self.cr, self.uid, partner)
        elif purchase.warehouse_id:
            return [purchase.warehouse_id.name]        
        return []  
    
    def _get_line_tax(self, line_obj):
        self.cr.execute("SELECT tax_id FROM purchase_order_taxe WHERE order_line_id=%s", (line_obj.id))
        res = self.cr.fetchall() or None
        if not res:
            return ""
        if isinstance(res, list):
            tax_ids = [t[0] for t in res]
        else:
            tax_ids = res[0]
        res = [tax.name for tax in self.pooler.get_pool(self.cr.dbname).get('account.tax').browse(self.cr, self.uid, tax_ids)]
        return ",\n ".join(res)
    
    def _get_tax(self, order_obj):
        self.cr.execute("SELECT DISTINCT tax_id FROM purchase_order_taxe, purchase_order_line, purchase_order \
            WHERE (purchase_order_line.order_id=purchase_order.id) AND (purchase_order.id=%s)", (order_obj.id))
        res = self.cr.fetchall() or None
        if not res:
            return []
        if isinstance(res, list):
            tax_ids = [t[0] for t in res]
        else:
            tax_ids = res[0]
        tax_obj = self.pooler.get_pool(self.cr.dbname).get('account.tax')
        res = []
        for tax in tax_obj.browse(self.cr, self.uid, tax_ids):
            self.cr.execute("SELECT DISTINCT order_line_id FROM purchase_order_line, purchase_order_taxe \
                WHERE (purchase_order_taxe.tax_id=%s) AND (purchase_order_line.order_id=%s)", (tax.id, order_obj.id))
            lines = self.cr.fetchall() or None
            if lines:
                if isinstance(lines, list):
                    line_ids = [l[0] for l in lines]
                else:
                    line_ids = lines[0]
                base = 0
                for line in self.pooler.get_pool(self.cr.dbname).get('purchase.order.line').browse(self.cr, self.uid, line_ids):
                    base += line.price_subtotal
                res.append({'code':tax.name,
                    'base':base,
                    'amount':base*tax.amount})
        return res
    
    def _get_product_code(self, product_id, partner_id):
        product_obj=self.pooler.get_pool(self.cr.dbname).get('product.product')
        return product_obj._product_code(self.cr, self.uid, [product_id], name=None, arg=None, context={'partner_id': partner_id})[product_id]