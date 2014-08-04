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

class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        "pos_printer": fields.char("POS-Printer", size=64),
        "printer_escpos" : fields.boolean("ESC/POS Network Printer"),             
        "balance_credit" : fields.boolean("Balance Credit",
                                help="If checked credit notes from customer are automatically reconciled if statement are closed\n"
                                      "this is an special option for customer credit note reconcilation"),
        "parent_id" : fields.many2one("account.journal","Parent",select=True,
                                      help="If an parent account is defined.\nStatement with this journal could only opened with "
                                      " an parent statement of the same journal"),
        "child_ids" : fields.one2many("account.journal","parent_id","Childs",select=True)
    }
account_journal()