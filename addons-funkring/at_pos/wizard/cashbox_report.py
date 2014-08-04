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

class cashbox_report_wizard(osv.osv_memory):
       
    def _get_period(self, cr, uid, context=None):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        return False
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}   
        wizard = self.browse(cr, uid, ids[0], context)     
        datas = {"ids": [wizard.period_id.id]}
        return {
            "type": "ir.actions.report.xml",
            "report_name": "at_pos.cashbox_period",
            "datas": datas,
            "context" : { "journal_id" : wizard.journal_id.id, "detail" : wizard.detail }
        }

    
    _name = "pos.cashbox_report.wizard"
    _description = "Cashbox Report Wizard"
    _columns = {
        "period_id" : fields.many2one("account.period", "Period", required=True),
        "journal_id" : fields.many2one("account.journal","Journal",required=True, domain=[("parent_id", "=", False)]),
        "detail" : fields.boolean("Attach Daily Cash Reports")
    }    
    
    _defaults = {
        'period_id': _get_period    
    }    
cashbox_report_wizard()