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

from dateutil.relativedelta import relativedelta
from openerp.addons.at_base import util

from openerp.report import report_sxw


class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'timesheet_lines': self.timesheet_lines
        })
        self.context = context
    
    def _get_lines(self, in_days, in_day): #Added "self" as first parameter, to avoid an error
        lines = in_days.get(in_day,None)
        if lines == None:
            lines = []
            in_days[in_day]=lines
        return lines
            
    def timesheet_lines(self, timesheet):
        
        class Attendances:
            def __init__(self,fromTime,toTime):
                self.fromTime = fromTime
                self.toTime = toTime             
                   
        class Lines:
            def __init__(self):
                self.day = None
                self.work = []
                self.attendance = []
                self.leaves = []                
                self.total = None
                self.total_timesheet = None
                self.total_saldo = None
                self.total_target = None
                
        timesheet_obj = self.pool.get("hr_timesheet_sheet.sheet")
        timesheet_line_obj = self.pool.get("hr.analytic.timesheet")
        
        data = timesheet_obj.get_timesheet_data(self.cr,timesheet.user_id.id,timesheet.id,context=self.context)
        lines = []
                
        date_from = util.strToDate(timesheet.date_from)
        date_to = util.strToDate(timesheet.date_to)
        date_cur = date_from
        delta_day = relativedelta(days=1)        
        
        while date_cur <= date_to:
            date_cur_str = util.dateToStr(date_cur)
            value = data.get(date_cur_str)
            if value:
                line = Lines()                                    
                line.day = date_cur_str    
                line.total =  value.get("total_attendance_day") or 0.0 
                line.total_timesheet = value.get("total_timesheet_day") or 0.0                
                line.total_saldo = value.get("total_saldo") or 0.0
                line.total_target = value.get("total_target") or 0.0
                
                attendance_lines = value.get("attendances")            
                if attendance_lines:
                    for attendance_line in attendance_lines:
                        date_only = attendance_line["to"].split(" ")[1]
                        if date_only != "24:00:00":
                            line.attendance.append(Attendances(util.timeToStrHours(attendance_line["from"]),util.timeToStrHours(attendance_line["to"])))
                work_lines = value.get("lines",None)
                if work_lines:
                    line.work = timesheet_line_obj.browse(self.cr,self.uid,work_lines,context=self.context)
                    
                
                leaves = value.get("leaves",None)
                if leaves:
                    line.leaves = leaves
                                               
                lines.append(line)                
            date_cur+=delta_day
                
        return lines           
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

