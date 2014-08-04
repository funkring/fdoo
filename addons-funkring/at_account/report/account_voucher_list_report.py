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
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "date_str" : self._date_str,
            "journal_str" : self._journal_str,
            "number_str" : self._number_str,
            "reference_str" : self._reference_str,
            "partner_str" : self._partner_str,
            "amount_str" : self._amount_str,
            "voucher_ref" : self._voucher_ref 
        })
        self.localcontext["report_title"] = context.get("report_title",_("Voucher overview"))
    
    def _voucher_ref(self, voucher):
        self.cr.execute(" SELECT inv.number, inv.reference FROM account_invoice inv "
                        "  INNER JOIN account_move m ON m.id = inv.move_id "
                        "  INNER JOIN account_move_line ml1 ON ml1.move_id = m.id "
                        "  INNER JOIN account_move_line ml2 ON (    ml2.reconcile_partial_id = ml1.reconcile_partial_id " 
                        "                                       OR ml2.reconcile_id = ml1.reconcile_id ) "
                        "                                 AND ml2.id != ml1.id "
                        "  INNER JOIN account_voucher v ON v.move_id = ml2.move_id "
                        "  INNER JOIN account_move m3 ON m3.id = v.move_id AND v.id = %s"
                        "  GROUP BY 1,2 ", (voucher.id,))
                         
        res = []
        for row in self.cr.fetchall():
            if row[0]:
                res.append(row[0])
            if row[1]:
                res.append(row[1])        
        if voucher.reference:
            res.append(voucher.reference)
        #            
        res = ", ".join(res)
        return res
    
    def _date_str(self):
        return _("Date")
    
    def _journal_str(self):
        return _("Journal")
    
    def _number_str(self):
        return _("Number")
    
    def _reference_str(self):
        return _("Reference")
    
    def _partner_str(self):
        return _("Partner")
    
    def _amount_str(self):
        return _("Amount")