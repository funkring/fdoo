# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.addons.at_base import util
from openerp.report import report_sxw


class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_sheet': self._get_sheet
        })
        self.context = context
    
    def _get_sheet(self, o):
        timesheet_obj = self.pool.get("hr_timesheet_sheet.sheet")
        sheet = None
        if o._name == "hr.employee":
            sheet = timesheet_obj._build_sheet(self.cr, self.uid, employee=o, context=self.localcontext)
        elif o._name == "hr_timesheet_sheet.sheet":                
            sheet = timesheet_obj._build_sheet(self.cr, self.uid, sheets=[o], context=self.localcontext)
        return sheet and [sheet] or []
