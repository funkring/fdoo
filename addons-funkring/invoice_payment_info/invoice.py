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

from openerp.osv import fields,osv

class account_invoice(osv.osv):
    
    def _last_payment_date(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute(
        """
        SELECT inv.id, MAX(m2.date) FROM account_invoice inv
            INNER JOIN account_move_line m ON m.move_id = inv.move_id AND m.account_id = inv.account_id
            INNER JOIN account_move_reconcile r ON r.id = m.reconcile_id 
            INNER JOIN account_move_line m2 ON m2.reconcile_id = r.id OR m2.reconcile_partial_id = r.id
            INNER JOIN account_journal j ON j.id = m2.journal_id AND j.type IN ('cash','bank')
            WHERE inv.id IN %s
        GROUP BY 1
        """, (tuple(ids),)
        )
        
        for row in cr.fetchall():
            invoice_id = row[0]
            date = row[1]
            res[invoice_id]=date
        
        return res
    
    def _payment_journal_names(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        
        ####################################################################
        cr.execute(
        """
        SELECT inv.id, j.name FROM account_invoice inv
            INNER JOIN account_move_line m ON m.move_id = inv.move_id AND m.account_id = inv.account_id
            INNER JOIN account_move_reconcile r ON r.id = m.reconcile_id 
            INNER JOIN account_move_line m2 ON m2.reconcile_id = r.id OR m2.reconcile_partial_id = r.id
            INNER JOIN account_journal j ON j.id = m2.journal_id AND j.type IN ('cash','bank')
            WHERE inv.id IN %s
        GROUP BY 1,2
        """, (tuple(ids),)
        )
        for row in cr.fetchall():
            invoice_id = row[0]
            journal_name = row[1]
            cur = res[invoice_id]
            if not cur:
                cur = []
                res[invoice_id]=cur
            cur.append(journal_name)
        for key, value in res.items():
            if value:
                res[key] = ", ".join(value)
        ####################################################################
        
        return res
    
    _inherit = "account.invoice" 
    _columns = {
        "last_payment_date" : fields.function(_last_payment_date, type="date", string="Last payment date"),
        "payment_journal_names" : fields.function(_payment_journal_names, type="char", size=128, string="Payment journal names")
    }
