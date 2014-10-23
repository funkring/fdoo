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

class working_report(osv.Model):
    _name = "working.report"
    _description = "Working Report"
    _columns = {
        "name" : fields.char("Name"),
        "description" : fields.text("Description"),
        "analytic_line_ids" : fields.many2many("account.analytic.line",
                                               "working_report_account_analytic_line_rel",
                                               "report_id", 
                                               "line_id", string="Work")
    }
    _defaults = {
        "name" : lambda self, cr, uid, context: self.pool.get("ir.sequence").get(cr, uid, "working.report") or "/"
    }