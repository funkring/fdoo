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
from openerp.tools.translate import _

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "bank_statement_lines" : self._bank_statement_lines,
            "name_str" : self._name_str,
            "date_str" : self._date_str,
            "journal_str" : self._journal_str,
            "balance_start_str" : self._balance_start_str,
            "balance_end_str" : self._balance_end_str,
            "amount_str" : self._amount_str,
            "partner_str" : self._partner_str,
            "account_str" : self._account_str,
            "date_invoice_str" : self._date_invoice_str
        })
        
    def _bank_statement_lines(self, statement):
        
        date_invoice = None
        statement_lines = []
        res = []
        statement_line_obj = self.pool.get("account.bank.statement.line")
        statement_line_ids = statement_line_obj.search(self.cr, self.uid, [("statement_id","=", statement.id)])
        
        for statement_line_id in statement_line_ids:
            statement_line = statement_line_obj.browse(self.cr, self.uid, statement_line_id)
            statement_lines.append(statement_line)
        
        for line in statement_lines:
            res_value = {}
            res_value["name"] = line.name
            res_value["date"] = line.date
            res_value["amount"] = line.amount
            res_value["partner_name"] = line.partner_id.name
            res_value["account_code"] = line.account_id.code
            res_value["account_name"] = line.account_id.name
            
            voucher = line.voucher_id
            if voucher:
                move_ids = [x.id for x in line.voucher_id.move_ids]
                if move_ids:
                    self.cr.execute("SELECT inv.date_invoice FROM account_invoice inv "
                        "    INNER JOIN account_move_line m ON m.move_id = inv.move_id AND m.account_id = inv.account_id "
                        "    INNER JOIN account_move_reconcile r ON r.id = m.reconcile_id "
                        "   INNER JOIN account_move_line m2 ON m2.reconcile_id = r.id OR m2.reconcile_partial_id = r.id "
                        "   WHERE m2.id in %s GROUP BY 1 ", (tuple(move_ids),))
                     
                    for row in self.cr.fetchall():
                        date_invoice=row[0]
                        break
               
            res_value["invoice_date"] = date_invoice
            res.append(res_value)
            
        return res
    
    def _name_str(self):
        return _("Name")
    
    def _date_str(self):
        return _("Date")
    
    def _journal_str(self):
        return _("Journal")
    
    def _balance_start_str(self):
        return _("Balance Start")
    
    def _balance_end_str(self):
        return _("Balance End")
    
    def _amount_str(self):
        return _("Amount")
    
    def _partner_str(self):
        return _("Partner")
    
    def _account_str(self):
        return _("Account")
        
    def _date_invoice_str(self):
        return _("Invoice Date")