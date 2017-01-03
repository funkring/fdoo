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
from openerp.addons.at_base import util
from datetime import datetime
from dateutil.relativedelta import relativedelta

class hr_timesheet_sheet_sheet_day(osv.osv):

    def _total_saldo(self, cr,uid, ids, field_name,arg,context=None):
        res = dict.fromkeys(ids)
        for daily_sheet in self.browse(cr, uid, ids, context):
            res[daily_sheet.id] = (daily_sheet.total_attendance or 0.0)-(daily_sheet.total_target or 0.0);
        return res

    def _total_target(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids,0.0)
        working_hour_obj = self.pool.get("resource.calendar")
        employee_obj = self.pool.get("hr.employee")
        for daily_sheet in self.browse(cr, uid, ids, context):
            sheet = daily_sheet.sheet_id
            date_from = daily_sheet.name
            date_to = util.dateToStr(util.getLastTimeOfDay(util.strToDate(date_from)))
            contract = employee_obj._get_contract(cr, uid, sheet.employee_id.id, date_from=date_from, date_to=date_to, context=context)
            if contract:               
                res[sheet.id] = working_hour_obj.interval_hours_without_leaves(cr,uid,contract["working_hours"],
                                                                        util.strToDate(contract["date_from"]),
                                                                        util.strtoDate(contract["date_to"]),
                                                                        sheet.employee_id.resource_id.id)
        return res


    _inherit = "hr_timesheet_sheet.sheet.day"
    _columns = {
       "total_saldo" : fields.function(_total_saldo,string="Saldo",readonly=True),
       "total_target" : fields.function(_total_target, string="Target",readonly=True),
    }

class hr_timesheet_sheet(osv.osv):

    def _build_sheet(self, cr, uid, date_from=None, date_to=None, months=None, employee=None, sheets=None, context=None):
        # check context date
        if not context is None:
            if not date_from:
                date_from = context.get("date_from")
            if not date_to:
                date_to = context.get("date_to")
        
        # check months
        if date_from and months:
            date_to = util.getNextDayOfMonth(date_from,inMonth=months)

        # if employ was passed        
        if employee:
            date_cur = util.currentDate()
            if not date_from:
                date_from = util.getFirstOfMonth(date_cur)
            if not date_to:
                date_to = util.getEndOfMonth(date_cur)

            cr.execute("SELECT s.id FROM hr_timesheet_sheet_sheet s "
                            " WHERE (( s.date_from <= %s AND s.date_to >= %s) "
                              "  OR  ( s.date_from <= %s AND s.date_to >= %s) "
                              "  OR  ( s.date_from >= %s AND s.date_to <= %s)) "
                              " AND s.employee_id = %s "
                              " ORDER BY s.date_from "
                            , (date_from, date_from, 
                               date_to, date_to, 
                               date_from, date_to, 
                               employee.id))
            
            sheet_ids = [r[0] for r in cr.fetchall()]
            sheets = self.browse(cr, uid, sheet_ids, context=context)
            
        # if sheets was passed
        elif sheets:
            if not date_from:
                date_from = sheets[0].date_from
            if not date_to:
                date_to = sheets[-1].date_to
            
        
        # return if no sheet
        if not sheets or not date_from or not date_to:
            return None
        
        cr.execute("SELECT s.id FROM hr_timesheet_sheet_sheet s "
                         " WHERE s.date_to = ( SELECT MAX(s2.date_to) FROM hr_timesheet_sheet_sheet s2 "
                                                                       " WHERE s2.date_to < %s AND s2.employee_id = s.employee_id )"
                           " AND s.employee_id = %s "
                           " ORDER BY s.date_from "
                         , (sheets[0].date_from, sheets[0].employee_id.id))
        
        query_res = cr.fetchall()
        sheet_before = None 
        if query_res:
            sheet_before = self.browse(cr, uid, query_res[0][0], context=context)
        
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
        timesheet_line_obj = self.pool.get("hr.analytic.timesheet")    
        for sheet in sheets:
            timesheet_data = self.get_timesheet_data(cr, sheet.user_id.id, sheet.id, context=context)
            
            sheet_dt_from = util.strToDate(sheet.date_from)
            sheet_dt_cur =  sheet_dt_from            
            sheet_dt_to = util.strToDate(sheet.date_to)
                        
            delta_day = relativedelta(days=1)    
    
            while sheet_dt_cur <= sheet_dt_to and sheet_dt_cur <= dt_to:
                date_day = util.dateToStr(sheet_dt_cur)
                timesheet_day = timesheet_data.get(date_day)
                if timesheet_day:                
                    # vars                    
                    day_saldo = timesheet_day.get("total_saldo") or 0.0
                    
                    # increment saldo
                    current_saldo+=day_saldo
                                             
                    # check if date is in date from
                    if sheet_dt_cur >= dt_from:
                        # get vars
                        day_total_timesheet = timesheet_day.get("total_timesheet_day") or 0.0
                        day_target = timesheet_day.get("total_target") or 0.0
                        day_attendance = timesheet_day.get("total_attendance_day") or 0.0
                        
                        # get attendance
                        attendance = []
                        attendance_text = []
                        attendance_lines = timesheet_day.get("attendances",None)            
                        if attendance_lines:
                            for attendance_line in attendance_lines:
                                timestamp_to = attendance_line["to"]
                                time_only = timestamp_to and timestamp_to.split(" ")[1] or None
                                if time_only != "24:00:00":
                                    time_from = util.timeToStrHours(attendance_line["from"])
                                    time_to = util.timeToStrHours(timestamp_to)
                                    attendance_text.append("%s - %s" % (time_from,time_to))
                                    attendance.append({
                                            "time_from" : time_from,
                                            "time_to" : time_to
                                    })
                        
                        # get work 
                        work = timesheet_line_obj.browse(cr, uid, timesheet_day.get("lines",[]), context=context)

                        # process leaves                        
                        leaves = timesheet_day.get("leaves",[])
                        leave_names = []               
                        for leave in leave_obj.browse(cr, uid, [l[0] for l in leaves], context=context):
                            leave_names.append(leave.name)
                            if leave.name:
                                attendance_text.append(leave.name)
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
                        
                        
                        # increment counters                        
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
                            "attendance_text" : "\n".join(attendance_text),
                            "work" : work,
                            "leaves" : leave_names,
                            "leaves_taken" : leaves_taken,
                            "remaining_leaves" : remaining_leaves,
                            "sick_leaves" : sick_leaves,
                            "sheet" : sheet
                        }
                        days.append(day)
                        
                    elif sheet_dt_cur < dt_from:
                        last_saldo = current_saldo
                
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

    def get_timesheet_data(self, cr, uid, oid, context=None):
        days = super(hr_timesheet_sheet,self).get_timesheet_data(cr, uid, oid, context=context)
        working_hour_obj = self.pool.get("resource.calendar")
        employee_obj = self.pool.get("hr.employee")
        sheet = self.browse(cr, uid, oid, context)
        for key,value in days.items():
            contract = employee_obj._get_contract(cr, uid, sheet.employee_id.id, date_from=key, date_to=key, context=context)
            if contract:
                dt = util.strToDate(key)
                value["total_target"]=working_hour_obj.interval_hours_without_leaves(cr, uid, contract["working_hours"].id,
                                                                    dt,
                                                                    dt,
                                                                    sheet.employee_id.resource_id.id) or 0.0
                value["total_saldo"]=(value.get("total_attendance_day") or 0.0)-value["total_target"]
        return days

    def get_leaves(self, cr, uid, sid, context=None):
        res = {}        
        sheet = self.browse(cr, uid, sid, context)
        employee_obj = self.pool.get("hr.employee")
        contract = employee_obj._get_contract(cr, uid, sheet.employee_id.id, date_from=sheet.date_from, date_to=sheet.date_to, context=context)
        if contract:
            cr.execute( "SELECT id, name, date_from, date_to FROM resource_calendar_leaves "
                        " WHERE resource_id = %s OR resource_id IS NULL "
                        "  AND  (    (date_from >= %s AND date_from <= %s) "
                                " OR (date_to >= %s AND date_to <= %s ) "
                                " OR (date_from <= %s AND date_to >= %s ) )",
                    (sheet.employee_id.resource_id.id,
                     sheet.date_from,sheet.date_to,
                     sheet.date_from,sheet.date_to,
                     sheet.date_from,sheet.date_to))


            for oid, name, leave_date_from, leave_date_to in cr.fetchall():

                date_from = util.timeToDateStr(leave_date_from)
                if date_from < sheet.date_from:
                    date_from = sheet.date_from

                date_to = util.timeToDateStr(leave_date_to)
                if date_to > sheet.date_to:
                    date_to = sheet.date_to

                d_datefrom = util.strToDate(date_from)
                d_dateto = util.strToDate(date_to)
                d_cur= d_datefrom
                d_delta = relativedelta(days=1)

                while d_cur <= d_dateto:
                    cur_date = util.dateToStr(d_cur)
                    leaves = res.get(cur_date)
                    if not leaves:
                        leaves = []
                        res[cur_date]=leaves

                    leaves.append((oid,name))
                    d_cur+=d_delta

        return res

    def _total_target(self,cr,uid,ids,name,arg,context=None):
        res = dict.fromkeys(ids,0.0)
        working_hour_obj = self.pool.get("resource.calendar")
        employee_obj = self.pool.get("hr.employee")
        for sheet in self.browse(cr, uid, ids, context):
            contract = employee_obj._get_contract(cr, uid, sheet.employee_id.id, date_from=sheet.date_from, date_to=sheet.date_to, context=context)
            if contract:
                res[sheet.id] = working_hour_obj.interval_hours_without_leaves(cr,uid,contract["working_hours"].id,
                                                                    util.strToDate(contract["date_from"]),
                                                                    util.strToDate(contract["date_to"]),
                                                                    sheet.employee_id.resource_id.id)
        return res

    def _total_current_target(self,cr,uid,ids,field_name,arg,context=None):
        res = dict.fromkeys(ids,0.0)
        working_hour_obj = self.pool.get("resource.calendar")
        employee_obj = self.pool.get("hr.employee")
        for sheet in self.browse(cr, uid, ids, context):
            contract = employee_obj._get_contract(cr, uid, sheet.employee_id.id, date_from=sheet.date_from, date_to=sheet.date_to, context=context)
            if contract:
                sheet_now = datetime.now()
                sheet_from = util.strToDate(sheet.date_from)
                sheet_to = util.strToDate(sheet.date_to)

                if sheet_to.date() < sheet_now.date() or not sheet_from.date() < sheet_now.date():
                    res[sheet.id] = working_hour_obj.interval_hours_without_leaves(cr, uid, contract["working_hours"].id,
                                                                        util.strToDate(contract["date_from"]),
                                                                        util.strToDate(contract["date_to"]),
                                                                        sheet.employee_id.resource_id.id)
                else:
                    res[sheet.id] = working_hour_obj.interval_hours_without_leaves(cr, uid, contract["working_hours"].id,
                                                                        util.strToDate(contract["date_from"]),
                                                                        util.strToDate(contract["date_to"]),
                                                                        sheet.employee_id.resource_id.id)
        return res

    def _current_saldo(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0.0)
        for sheet in self.browse(cr, uid, ids, context):
            if sheet.state == "new" or sheet.state == "draft":
                saldo =  sheet.saldo_correction + (sheet.total_attendance-sheet.total_target)
                # add previous sheet saldo
                prev_ids = self.search(cr, 1, [('employee_id','=',sheet.employee_id.id),('date_to','<=',sheet.date_from)],limit=1,order='date_from desc')
                if prev_ids:
                    prev_sheet = self.read(cr, uid, prev_ids[0], ["current_saldo"])
                    saldo = saldo + prev_sheet["current_saldo"]

                res[sheet.id] = saldo
            else:
                res[sheet.id] = sheet.saldo

        return res

    def _last_saldo(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for sheet in self.browse(cr, uid, ids, context):
            res[sheet.id] = 0.0
            # add previous sheet saldo
            prev_ids = self.search(cr, 1, [('employee_id','=',sheet.employee_id.id),('date_to','<=',sheet.date_from)],limit=1,order='date_from desc')
            if prev_ids:
                prev_sheet = self.browse(cr, uid, prev_ids[0], context)
                res[sheet.id] = prev_sheet.current_saldo
        return res


    def _total_holiday(self, cr, uid, ids, field_names, arg, context=None):
        res = dict.fromkeys(ids,None)
        holidays_status_obj = self.pool.get("hr.holidays.status")
        for sheet in self.browse(cr, uid, ids, context):
            res[sheet.id] = {}
            status_ids = holidays_status_obj.search(cr,uid,[('categ_id.leave_type','=','holiday')])
            days = holidays_status_obj.get_days_sum(cr, uid,status_ids, sheet.employee_id.id, context=context)
            res[sheet.id]["max_leaves"] = days["max_leaves"]
            res[sheet.id]["leaves_taken"] = days["leaves_taken"]
            res[sheet.id]["remaining_leaves"] = days["remaining_leaves"]
        return res

    def _total_sick_leaves(self, cr, uid, ids, field_names, arg, context=None):
        res = dict.fromkeys(ids,None)
        holidays_status_obj = self.pool.get("hr.holidays.status")
        for sheet in self.browse(cr, uid, ids, context):
            res[sheet.id] = {}
            status_ids = holidays_status_obj.search(cr,uid,[('categ_id.leave_type','=','sickness')])
            days = holidays_status_obj.get_days_sum(cr, uid,status_ids, sheet.employee_id.id, context=context)
            res[sheet.id] = days["leaves_taken"]
        return res

    def update_saldo(self, cr, uid, sid, context=None):
        sheet = self.browse(cr, uid, sid, context)
        if sheet.saldo != sheet.current_saldo:
            self.write(cr, uid, sid, {"saldo" : sheet.current_saldo }, context)

        next_ids = self.search(cr, 1, ['&',('employee_id','=',sheet.employee_id.id),('date_from','>=',sheet.date_to)],limit=1,order='date_from')
        for next_id in next_ids:
            self.update_saldo(cr,uid,next_id,context)

    def button_confirm(self, cr, uid, ids, context=None):
        for sid in ids:
            self.update_saldo(cr,uid,sid,context)
        return super(hr_timesheet_sheet,self).button_confirm(cr,uid,ids,context)

    _inherit = "hr_timesheet_sheet.sheet"
    _columns = {
        "saldo" : fields.float('Saldo',readonly=True),
        "saldo_correction" : fields.float("Correction",readonly=True, states={'draft':[('readonly', False)]}),
        "current_saldo" : fields.function(_current_saldo, string="Current Saldo"),
        "last_saldo" : fields.function(_last_saldo,string="Last Saldo"),
        "total_target" : fields.function(_total_target, string="Target"),
        "total_current_target" : fields.function(_total_current_target, string="Current Target"),
        "max_leaves" : fields.function(_total_holiday,string="Total Holidays",multi="total_holiday"),
        "leaves_taken" : fields.function(_total_holiday,string="Holiday Taken",multi="total_holiday"),
        "remaining_leaves" : fields.function(_total_holiday,string="Remaining Holidays",multi="total_holiday",help="Current remaining holidays, is calculated over all"),
        "sick_leaves" : fields.function(_total_sick_leaves,string="Sick Leaves Taken"),
    }
