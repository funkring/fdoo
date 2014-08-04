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
        for daily_sheet in self.browse(cr, uid, ids, context):
            sheet = daily_sheet.sheet_id
            working_hours = sheet.employee_id.working_hours
            if working_hours:
                date_from = util.strToDate(sheet.date_current)
                date_to = util.getLastTimeOfDay(date_from)
                res[sheet.id] = working_hour_obj.interval_hours_without_leaves(cr,uid,working_hours.id,
                                                                        date_from,
                                                                        date_to,
                                                                        sheet.employee_id.resource_id.id)
        return res
    
    
    _inherit = "hr_timesheet_sheet.sheet.day"
    _columns = {
       "total_saldo" : fields.function(_total_saldo,string="Saldo",readonly=True),
       "total_target" : fields.function(_total_target, string="Target",readonly=True),
    }

class hr_timesheet_sheet(osv.osv):    
        
    def get_timesheet_data(self, cr, uid, oid, context=None):
        days = super(hr_timesheet_sheet,self).get_timesheet_data(cr, uid, oid, context=context)
        working_hour_obj = self.pool.get("resource.calendar")
        sheet = self.browse(cr, uid, oid, context)        
        for key,value in days.items():
            working_hours = sheet.employee_id.working_hours
            if working_hours:                
                value["total_target"]=working_hour_obj.interval_hours_without_leaves(cr,uid,working_hours.id,
                                                                    util.strToDate(key),
                                                                    util.strToDate(key),
                                                                    sheet.employee_id.resource_id.id) or 0.0
                value["total_saldo"]=(value.get("total_attendance_day") or 0.0)-value["total_target"]
        return days
        
    def get_leaves(self,cr,uid,sid,context=None):
        res = {}
        sheet = self.browse(cr, uid, sid, context)
        working_hours = sheet.employee_id.working_hours
        if working_hours:
            cr.execute( "SELECT name, date_from, date_to FROM resource_calendar_leaves "
                        " WHERE resource_id = %s OR resource_id IS NULL " 
                        "  AND  (    (date_from >= %s AND date_from <= %s) "
                                " OR (date_to >= %s AND date_to <= %s ) "
                                " OR (date_from <= %s AND date_to >= %s ) )", 
                    (sheet.employee_id.resource_id.id,
                     sheet.date_from,sheet.date_to,
                     sheet.date_from,sheet.date_to,
                     sheet.date_from,sheet.date_to))
                
                
            for row in cr.fetchall():
                name = row[0]
                
                date_from = util.timeToDateStr(row[1])
                if date_from < sheet.date_from:
                    date_from = sheet.date_from
                                
                date_to = util.timeToDateStr(row[2])
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
                        
                    leaves.append(name)                    
                    d_cur+=d_delta

        return res
    
    def _total_target(self,cr,uid,ids,name,arg,context=None):
        res = {}
        working_hour_obj = self.pool.get("resource.calendar")
        for sheet in self.browse(cr, uid, ids, context):
            res[sheet.id] = 0.0
            working_hours = sheet.employee_id.working_hours
            if working_hours:                
                res[sheet.id] = working_hour_obj.interval_hours_without_leaves(cr,uid,working_hours.id,
                                                                    util.strToDate(sheet.date_from),
                                                                    util.strToDate(sheet.date_to),
                                                                    sheet.employee_id.resource_id.id)                
        return res              
        
    def _total_current_target(self,cr,uid,ids,field_name,arg,context=None):
        res = {}
        working_hour_obj = self.pool.get("resource.calendar")
        for sheet in self.browse(cr, uid, ids, context):            
            res[sheet.id] = 0.0
            working_hours = sheet.employee_id.working_hours
            if working_hours:
                sheet_now = datetime.now()                
                sheet_from = util.strToDate(sheet.date_from)
                sheet_to = util.strToDate(sheet.date_to)
                
                if sheet_to.date() < sheet_now.date() or not sheet_from.date() < sheet_now.date():                
                    res[sheet.id] = working_hour_obj.interval_hours_without_leaves(cr,uid,working_hours.id,
                                                                        sheet_from,
                                                                        sheet_to,
                                                                        sheet.employee_id.resource_id.id)
                else:
                    res[sheet.id] = working_hour_obj.interval_hours_without_leaves(cr,uid,working_hours.id,
                                                                        sheet_from,
                                                                        sheet_now,
                                                                        sheet.employee_id.resource_id.id)                
        return res
                       
    def _current_saldo(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
                
        total_sums = super(hr_timesheet_sheet,self)._total(cr,uid,ids,field_name,arg,context)        
        total_current_targets = self._total_current_target(cr, uid, ids, field_name, arg, context)
        
        for sheet in self.browse(cr, uid, ids, context):            
            if sheet.state == "new" or sheet.state == "draft":                
                saldo =  sheet.saldo_correction + (total_sums[sheet.id]['total_attendance']-total_current_targets[sheet.id])                
                # add previous sheet saldo
                prev_ids = self.search(cr, 1, ['&',('employee_id','=',sheet.employee_id.id),('date_to','<=',sheet.date_from)],limit=1,order='date_from desc')
                if prev_ids:
                    prev_sheet = self.browse(cr, uid, prev_ids[0], context)
                    saldo = saldo + prev_sheet.current_saldo            
                
                res[sheet.id] = saldo
                    
            else:
                res[sheet.id] = sheet.saldo
        
        return res
        
    def _last_saldo(self, cr, uid, ids, field_name, arg, context=None):
        res = {}        
        for sheet in self.browse(cr, uid, ids, context):
            res[sheet.id] = 0.0
            # add previous sheet saldo
            prev_ids = self.search(cr, 1, ['&',('employee_id','=',sheet.employee_id.id),('date_to','<=',sheet.date_from)],limit=1,order='date_from desc')
            if prev_ids:
                prev_sheet = self.browse(cr, uid, prev_ids[0], context)
                res[sheet.id] = prev_sheet.current_saldo
        return res
    
  
    def _total_holiday(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        holidays_status_obj = self.pool.get("hr.holidays.status")
        for sheet in self.browse(cr, uid, ids, context):
            res[sheet.id] = {}
            status_ids = holidays_status_obj.search(cr,uid,[('categ_id.leave_type','=','holiday')])       
            days = holidays_status_obj.get_days_sum(cr,uid,status_ids,sheet.employee_id.id,False,context)                        
            res[sheet.id]["max_leaves"] = days["max_leaves"]
            res[sheet.id]["leaves_taken"] = days["leaves_taken"]
            res[sheet.id]["remaining_leaves"] = days["remaining_leaves"]        
        return res
    
    def _total_sick_leaves(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        holidays_status_obj = self.pool.get("hr.holidays.status")
        for sheet in self.browse(cr, uid, ids, context):
            res[sheet.id] = {}
            status_ids = holidays_status_obj.search(cr,uid,[('categ_id.leave_type','=','sickness')])       
            days = holidays_status_obj.get_days_sum(cr,uid,status_ids,sheet.employee_id.id,False,context)
            res[sheet.id]["leaves_taken"] = days["leaves_taken"]
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
        "remaining_leaves" : fields.function(_total_holiday,string="Remaining Holidays",multi="total_holiday"),
        "sick_leaves" : fields.function(_total_sick_leaves,string="Sick Leaves Taken"),
    }
