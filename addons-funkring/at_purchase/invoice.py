# -*- coding: utf-8 -*-

#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martinr@funkring.net>
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

from openerp.osv import osv,fields

class account_invoice_line(osv.osv):
    
    def _purchase_price(self, cr, uid, oid, context=None):        
        cr.execute("SELECT plrel.invoice_id, l.price_unit FROM sale_order_line_invoice_rel as rel " 
                   " INNER JOIN purchase_order_line AS pl ON pl.sale_order_line_id = rel.order_line_id "                   
                   " INNER JOIN purchase_order_line_invoice_rel AS plrel ON plrel.order_line_id = pl.id "
                   " INNER JOIN account_invoice_line AS l ON l.id = plrel.invoice_id "
                   " WHERE rel.invoice_id = %s" , (oid,) )
        
        res = None
        for row in cr.fetchall():
            res = {
                "price" : row[1],
                "invoice_line_id" : row[0],       
            }           
        return res
    
    def copy_data(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}
            
        if not default.has_key("purchase_lines"):
            default["purchase_lines"] = []
            
        return osv.osv.copy_data(self, cr, uid, oid, default=default, context=context)
    
    _inherit = "account.invoice.line"
    _columns = {
        "purchase_lines": fields.many2many("purchase.order.line", "purchase_order_line_invoice_rel", "invoice_id", 'order_line_id', "Invoice Lines", readonly=True)       
    }
