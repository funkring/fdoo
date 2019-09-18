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

from openerp.osv import osv

class account_invoice(osv.osv):
    
    def action_cancel(self, cr, uid, ids, context=None):
        ids_tuple=tuple(ids)
        
        cr.execute("SELECT sl.salesman_id FROM sale_order_line_invoice_rel rel  "
                   " INNER JOIN sale_order_line sl ON sl.id = rel.order_line_id "
                   " INNER JOIN sale_order o ON o.id = sl.order_id "
                   " WHERE      rel.invoice_id = %s " 
                   "       AND  sl.salesman_id IS NOT NULL " 
                   " GROUP BY 1 ", (ids_tuple,))
        
        salesman_ids = [r[0] for r in cr.fetchall()]
        
        cr.execute("SELECT inv.period_id FROM account_invoice inv"
                   " WHERE inv.id IN %s " 
                   " GROUP BY 1 ", (ids_tuple,))
                
        period_ids = [r[0] for r in cr.fetchall()]
        
        res = super(account_invoice,self).action_cancel(cr, uid, ids, context=context)        
        commission_line_obj = self.pool.get("commission.line")
        commission_line_obj._update_bonus(cr, uid, salesman_ids, period_ids, context=context)
        return res
        
    def confirm_paid(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).confirm_paid(cr, uid, ids, context=context)        
        self.pool["commission.task"]._recalc_sale_commission_invoice(cr, uid, domain=[("id","in",ids)], context=context)
        return res
  
    
    _inherit = "account.invoice"
