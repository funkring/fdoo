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

from openerp import models, fields, api, _
from openerp.addons.at_base import util

class WorkingTimeWizard(models.TransientModel):
    _name = "at_timereg.working.time.wizard"
    _description = "Working Time Wizard"
        
    date = fields.Date("Date", default=lambda self: util.getFirstOfLastMonth(), required=True, help="Create working report from date, always the first day of the select month was taken")
    months = fields.Integer("Months", default=1, required=True, help="How many month should the report include")
    
    def _report_action(self, name):
        report_context = self._context and dict(self._context) or {}
        
        date_from = util.getFirstOfMonth(self.date)
        date_to = util.getNextDayOfMonth(date_from,inMonth=self.months)
         
        return {
            "type" : "ir.actions.report.xml",
            "report_name" : name,
            "context" : {
                "active_ids" : self._context.get("active_ids"),
                "active_model" : self._context.get("active_model"),
                "date_from" : date_from,
                "date_to" : date_to
             }
        }
    
    @api.multi
    def action_print_working_time(self):
        for wizard in self:
            return wizard._report_action("at_timereg.employee.working")
    
    @api.multi
    def action_print_time_only(self):
        for wizard in self:
            return wizard._report_action("at_timereg.employee.time")
