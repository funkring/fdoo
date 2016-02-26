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

class account_bank_statement_line(osv.Model):
    _inherit = "account.bank.statement.line"
    
    def confirm_statement(self, cr, uid, ids, context=None):
        st_obj = self.pool.get("account.bank.statement")
        move_obj = self.pool.get('account.move')
        for st_line in self.browse(cr, uid, ids, context=context):
            move_ids = []
            if not st_line.amount:
                continue
            if st_line.account_id and not st_line.journal_entry_id.id:
                #make an account move as before
                vals = {
                    'debit': st_line.amount < 0 and -st_line.amount or 0.0,
                    'credit': st_line.amount > 0 and st_line.amount or 0.0,
                    'account_id': st_line.account_id.id,
                    'name': st_line.name
                }
                self.process_reconciliation(cr, uid, st_line.id, [vals], context=context)
            
            if st_line.journal_entry_id:
                move_ids.append(st_line.journal_entry_id.id)
            
        if move_ids:
            move_obj.post(cr, uid, move_ids, context=context)
        return True

