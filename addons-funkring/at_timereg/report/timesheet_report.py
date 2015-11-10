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
            'get_sheet': self._get_sheet
        })
        self.context = context
    
    def _build_sheet(self, sheet_before, sheets, date_from, date_to):
        days = []
        res = {
            "date_from" : date_from,
            "date_to" : date_to,
            "days" : days,
            "employee" : sheets[0].employee_id
        }

        dt_to = util.strToDate(date_to)
        dt_from = util.strToDate(date_from)
        
        total_timesheet = 0.0
        total_target = 0.0
        total = 0.0
        total_saldo = 0.0
        current_saldo = 0.0
        leaves_taken = 0.0        
        sick_leaves = 0.0
        last_saldo = 0.0
        
        remaining_leaves = sheets[0].remaining_leaves
        max_leaves = sheets[0].remaining_leaves
            
        if sheet_before:
            current_saldo = sheet_before.current_saldo
            last_saldo = current_saldo
    
        leave_obj = self.pool.get("resource.calendar.leaves")
        timesheet_obj = self.pool.get("hr_timesheet_sheet.sheet")
        timesheet_line_obj = self.pool.get("hr.analytic.timesheet")    
        for sheet in sheets:
            timesheet_data = timesheet_obj.get_timesheet_data(self.cr, sheet.user_id.id, sheet.id, context=self.context)
            
            sheet_dt_from = util.strToDate(sheet.date_from)
            sheet_dt_to = util.strToDate(sheet.date_to)
            sheet_dt_cur =  util.strToDate(date_from)
            delta_day = relativedelta(days=1)    
    
            while sheet_dt_cur <= sheet_dt_to and sheet_dt_cur < dt_to:
                date_day = util.dateToStr(sheet_dt_cur)
                timesheet_day = timesheet_data.get(date_day)
                
                # vars
                day_total_timesheet = timesheet_day.get("total_timesheet_day") or 0.0
                day_saldo = timesheet_day.get("total_saldo") or 0.0
                day_target = timesheet_day.get("total_target") or 0.0
                day_attendance = timesheet_day.get("total_attendance_day") or 0.0
                current_saldo+=day_saldo

                attendance = []
                attendance_lines = timesheet_day.get("attendances",None)            
                if attendance_lines:
                    for attendance_line in attendance_lines:
                        date_only = attendance_line["to"].split(" ")[1]
                        if date_only != "24:00:00":
                            attendance.append({
                                    "time_from" : util.timeToStrHours(attendance_line["from"]),
                                    "time_to" : util.timeToStrHours(attendance_line["to"])
                            })
                
                work = timesheet_line_obj.browse(self.cr, self.uid, timesheet_day.get("lines",[]), context=self.context)
                leaves = timesheet_day.get("leaves",[])
                
                leave_names = []               
                for leave in leave_obj.browse(self.cr, self.uid, [l[0] for l in leaves], context=self.context):
                    leave_names.append(leave.name)
                    holiday = leave.holiday_id
                    holiday_status = holiday.holiday_status_id
                    if holiday_status:
                        holiday_categ = holiday_status.categ_id                    
                        if holiday_categ:
                            if holiday_categ.leave_type == "holiday":
                                leaves_taken+=1
                            if holiday_categ.leave_type == "sickness":
                                sick_leaves+=1
                    # ONLY ONE LEAVE per DAY
                    break
                      
                if sheet_dt_cur >= dt_from:
                    total_timesheet += day_total_timesheet
                    total_target += day_target
                    total += day_attendance
                    total_saldo += day_saldo
                    day = {
                        "day" : date_day,
                        "total_timesheet" : day_total_timesheet,  
                        "total" : day_attendance,
                        "total_saldo" : day_saldo,
                        "total_target" : day_target,
                        "current_saldo" : current_saldo,
                        "attendance" : attendance,
                        "work" : work,
                        "leaves" : leave_names,
                        "leaves_taken" : leaves_taken,
                        "remaining_leaves" : remaining_leaves,
                        "sick_leaves" : sick_leaves
                    }
                    days.append(day)
                
                # next day
                sheet_dt_cur+=delta_day
                    
        res["max_leaves"] = max_leaves
        res["last_saldo"] = last_saldo
        res["current_saldo"] = current_saldo      
        res["leaves_taken"] = leaves_taken
        res["remaining_leaves"] = remaining_leaves
        res["total_timesheet"] = total_timesheet
        res["total_target"] = total_target
        res["sick_leaves"] = sick_leaves
        res["total"] = total
        res["total_saldo"] = total_saldo
        return res
    
    def _get_sheet(self, o):
        date_from = self.localcontext.get("date_from")
        date_to = self.localcontext.get("date_to")
        
        timesheet_obj = self.pool.get("hr_timesheet_sheet.sheet")
        sheets = None
        sheet_before = None
        
        if o._name == "hr.employee":
            # check date
            date_cur = util.currentDate()
            if not date_from:
                date_from = util.getFirstOfMonth(date_cur)
            if not date_to:
                date_to = util.getEndOfMonth(date_cur)

            sheet_obj = self.pool["hr_timesheet_sheet.sheet"]
            
            self.cr.execute("SELECT s.id FROM hr_timesheet_sheet_sheet s "
                            " WHERE s.date_from = ( SELECT MAX(s2.date_from) FROM hr_timesheet_sheet_sheet s2 "
                                                                            " WHERE s2.date_from <= %s AND s2.employee_id = %s )"
                              " AND s.date_to = ( SELECT MIN(s2.date_to) FROM hr_timesheet_sheet_sheet s2 "
                                                                          " WHERE s2.date_to <= %s )"
                              " AND s.employee_id = %s "
                              " ORDER BY s.date_from "
                            , (start_date, end_date, o.id))
            
            sheet_ids = [r[0] for r in self.cr.fetchall()]
            sheets = timesheet_obj.browse(self.cr, self.uid, sheet_ids, context=self.localcontext)
            
        elif o._name == "hr_timesheet_sheet.sheet":                
            if not date_from:
                date_from = o.date_from
            if not date_to:
                date_to = o.date_to
            sheets = [o]

        # get sheet before        
        if sheets:
           self.cr.execute("SELECT s.id FROM hr_timesheet_sheet_sheet s "
                            " WHERE  s.date_to = ( SELECT MAX(s2.date_to) FROM hr_timesheet_sheet_sheet s2 "
                                                                          " WHERE s2.date_to < %s )"
                              " AND s.employee_id = %s "
                              " ORDER BY s.date_from "
                            , (sheets[0].date_from, sheets[0].employee_id.id))
           query_res = self.cr.fetchall()
           if query_res:
               sheet_before = timesheet_obj.browse(self.cr, self.uid, query_res[0][0], context=self.localcontext)
        
           # build sheets
           return [self._build_sheet(sheet_before, sheets, date_from, date_to)]
        
        return []
    
