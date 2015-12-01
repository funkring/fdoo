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

class account_invoice_report(osv.osv):
    _inherit = 'account.invoice.report'
    _columns = {
        'root_analytic_id': fields.many2one('account.analytic.account', 'Main Analytic Account', readonly=True),
    }
    _depends = {
        'account.invoice.line': ['account_analytic_id'],
    }
    
    def _from(self):
        return super(account_invoice_report, self)._from() + """
                LEFT JOIN account_analytic_account aa ON aa.id = ail.account_analytic_id
        """

    def _select(self):
        return  super(account_invoice_report, self)._select() + ", sub.root_analytic_id as root_analytic_id"

    def _sub_select(self):
        return  super(account_invoice_report, self)._sub_select() + ", aa.root_account_id as root_analytic_id"

    def _group_by(self):
        return super(account_invoice_report, self)._group_by() + ", aa.root_account_id"
