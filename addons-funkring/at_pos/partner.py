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

class res_partners(osv.osv):
    
    def _calculated_balance(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids,0.0)
        for partner in self.browse(cr, uid, ids, context):
            balance = -(partner.credit)
            res[partner.id]=balance
                        
        cr.execute("SELECT l.partner_id, SUM(l.amount) FROM account_bank_statement_line l "
                   " INNER JOIN account_bank_statement s ON s.id = l.statement_id AND s.state = 'open' "
                   " INNER JOIN account_journal j ON j.id = s.journal_id AND j.balance_credit "
                   " WHERE l.partner_id IN %s " 
                   " GROUP BY 1 ", (tuple(ids),))
        
        for row in cr.fetchall():
            res[row[0]]-=row[1]

        return res
    
    _inherit = "res.partner"
    _columns = {
        "calculated_balance" : fields.function(_calculated_balance,type="float",digits_compute=dp.get_precision('Account'),
                                               string="Calculated Balance"),
    }
res_partners()