# -*- coding: utf-8 -*-
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

from openerp.osv import fields, osv

class sale_order_report(osv.Model):
    
    def _select(self):
        select_str = super(sale_order_report, self)._select()
        select_str += """
                ,o.margin AS margin 
                ,( SELECT SUM(invl.price_subtotal) FROM account_invoice_line invl
                   INNER JOIN account_invoice inv ON inv.id =  invl.invoice_id
                   WHERE invl.account_analytic_id = o.project_id
                     AND inv.type = 'out_invoice'  
                     AND inv.state NOT IN ('cancel','draft') 
                 ) AS inv_out
                ,( SELECT SUM(invl.price_subtotal) FROM account_invoice_line invl
                   INNER JOIN account_invoice inv ON inv.id = invl.invoice_id
                   WHERE invl.account_analytic_id = o.project_id
                     AND inv.type = 'out_invoice'  
                     AND inv.state = 'draft'  
                 ) AS inv_draft_out
                ,( SELECT SUM(invl.price_subtotal) FROM account_invoice_line invl
                   INNER JOIN account_invoice inv ON inv.id =  invl.invoice_id
                   WHERE invl.account_analytic_id = o.project_id
                     AND inv.type = 'in_invoice'  
                     AND inv.state NOT IN ('cancel','draft')                   
                 ) AS inv_in
                ,( SELECT SUM(invl.price_subtotal) FROM account_invoice_line invl
                   INNER JOIN account_invoice inv ON inv.id =  invl.invoice_id
                   WHERE invl.account_analytic_id = o.project_id
                     AND inv.type = 'in_invoice'  
                     AND inv.state = 'draft'                
                 ) AS inv_draft_in
                 """
        return select_str
    
    def _group_by(self):
        group_by_str = super(sale_order_report, self)._group_by()
        group_by_str += """
                ,o.margin
        """
        return group_by_str
    
    _inherit = "sale.order.report"
    _columns = {
        "inv_out": fields.float("Customer Invoice", readonly=True),
        "inv_draft_out": fields.float("Customer Invoice (Draft)", readonly=True),
        "inv_in" : fields.float("Supplier Invoice", readonly=True),
        "inv_draft_in" : fields.float("Supplier Invoice (Draft)", readonly=True),
        "margin" : fields.float("Pre Calculation", readonly=True)
    }