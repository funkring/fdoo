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
import openerp.addons.decimal_precision as dp
from openerp.addons.at_base import util
from openerp.addons.at_base import helper
from dateutil.relativedelta import relativedelta

class hr_timesheet(osv.osv):        
    
    def add_totals_day(self, cr, uid, oid, days, context=None):
        res = {}
        cr.execute('SELECT day.name, day.total_attendance, day.total_timesheet, day.total_difference\
                FROM hr_timesheet_sheet_sheet AS sheet \
                LEFT JOIN hr_timesheet_sheet_sheet_day AS day \
                    ON (sheet.id = day.sheet_id \
                        AND day.name IN %s) \
                WHERE sheet.id = %s',(tuple(days),oid) )
        for record in cr.fetchall():
            res[record[0]] = {}
            res[record[0]]['total_attendance_day'] = record[1]
            res[record[0]]['total_timesheet_day'] = record[2]
            res[record[0]]['total_difference_day'] = record[3]
        return res
    
    
    def get_leaves(self,cr,uid,oid,context=None):                  
        return {}
    
    def _get_date_from(self,cr, uid, str_date, context=None):
        d_date = util.strToDate(str_date)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r=='month':
            return d_date.strftime('%Y-%m-01')
        elif r=='week':
            return (d_date + relativedelta(weekday=0, weeks=-1)).strftime('%Y-%m-%d')
        elif r=='year':
            return d_date.strftime('%Y-01-01')
        return d_date.strftime('%Y-%m-%d')

    def _get_date_to(self,cr, uid, str_date, context=None):
        d_date = util.strToDate(str_date)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r=='month':
            return (d_date + relativedelta(months=+1,day=1,days=-1)).strftime('%Y-%m-%d')
        elif r=='week':
            return (d_date + relativedelta(weekday=6)).strftime('%Y-%m-%d')
        elif r=='year':
            return d_date.strftime('%Y-12-31')
        return d_date.strftime('%Y-%m-%d')
    
    def get_timesheet_day(self,cr,uid,str_date,context=None):
        """
            return ts_day_obj
        """
        if context is None:
            context = {}        
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if employee_ids:
            employee_id = employee_ids[0]        
            timesheet_ids = self.search(cr, uid, [('employee_id','=',employee_id),('state','in',['draft','new']),('date_from','<=',str_date), ('date_to','>=',str_date)], context=context)
            if timesheet_ids:
                ts_day_obj = self.pool.get("hr_timesheet_sheet.sheet.day")
                ts_day_ids = ts_day_obj.search(cr,uid,[("name","=",str_date),("sheet_id","=",timesheet_ids[0])])
                if ts_day_ids:
                    return ts_day_obj.browse(cr,uid,ts_day_ids[0],context)                
        return None       
        
    def get_timesheet(self,cr,uid,str_date,context=None):
        if context is None:
            context = {}        
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if employee_ids:
            employee_id = employee_ids[0]        
            timesheet_ids = self.search(cr, uid, [('employee_id','=',employee_id),('date_from','<=',str_date), ('date_to','>=',str_date)], context=context)
            if timesheet_ids:
                return timesheet_ids[0]
        return None            
        
    def get_timesheet_lazy(self,cr,uid,str_date,context=None):
        if context is None:
            context = {}
        
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if not len(employee_ids):
            raise osv.except_osv(_('Error !'), _('No employee defined for your user !'))
        elif len(employee_ids) > 1:
            raise osv.except_osv(_('Error !'), _('More than one employee defined for your user !'))
        
        employee_id = employee_ids[0]        
        timesheet_ids = self.search(cr, uid, [('employee_id','=',employee_id),('state','in',['draft','new']),('date_from','<=',str_date), ('date_to','>=',str_date)], context=context)
        if len(timesheet_ids) > 1:
            raise osv.except_osv(_('Error !'), _('More than one timesheet for the same user and the same time range !'))
        elif len(timesheet_ids) == 1:
            return timesheet_ids[0]
        else:
            date_from = self._get_date_from(cr,uid,str_date,context)
            vals = {
                "name" : helper.getMonthYear(cr, uid, str_date, context),
                "date_from" : date_from,
                "date_to" : self._get_date_to(cr,uid,str_date,context),
                "date_current" : date_from,      
                "state" : "new",
                "employee_id" : employee_id,
                "company_id" : self.pool.get('res.company')._company_default_get(cr, uid, 'hr_timesheet_sheet.sheet', context=context)            
            }
            return self.create(cr, uid, vals, context=context)
      
        
    def get_timesheet_data(self, cr, uid, oid, context=None):        
        #inner function for get lines
        def _get_attendances(in_days, in_day):
            data = in_days.get(in_day,None)
            if data == None:
                data = {}
                in_days[in_day] = data
                
            attendance = data.get("attendances",None)
            if attendance == None:
                attendance = []
                in_days[in_day]["attendances"]=attendance
                                
            return attendance
                
        timesheet = self.browse(cr, uid, oid, context)          
        attendance_obj = self.pool.get("hr.attendance")
        attendance_ids = attendance_obj.search(cr,uid,[("sheet_id","=",timesheet.id)],order="name asc")
        
        next_range = {
            "day" : None,
            "from" : None,
            "to" : None            
        }
                         
        days = {}        
        for att in attendance_obj.browse(cr,uid,attendance_ids,context):
            cur_day = att.day            
            if att.action == "sign_in":                    
                next_range = {
                 "day" : cur_day,
                 "from" : helper.strToLocalTimeStr(cr,uid,att.name,context),
                 "to" : None              
                }                                                     
                _get_attendances(days,cur_day).append(next_range)
            elif att.action=="sign_out":
                if next_range["day"] != cur_day:
                    next_range = {
                      "day" : cur_day,
                      "from" : None,
                      "to" : helper.strToLocalTimeStr(cr,uid,att.name,context)
                    }                
                    _get_attendances(days,cur_day).append(next_range)
                else:
                    next_range["to"] = helper.strToLocalTimeStr(cr,uid,att.name,context)
                    
                    
        leaves = self.get_leaves(cr, uid, oid, context)
        date_from = util.strToDate(timesheet.date_from)
        date_to = util.strToDate(timesheet.date_to)
        date_cur = date_from
        delta_day = relativedelta(days=1)
        range_open = False
        
        while date_cur <= date_to:
            date_cur_str = util.dateToStr(date_cur)     
            attendances = _get_attendances(days,date_cur_str)
            
            days[date_cur_str]['total_attendance_day']=0.0
            days[date_cur_str]['total_timesheet_day']=0.0
            days[date_cur_str]['total_difference_day']=0.0
            
            leaves_for_day = leaves.get(date_cur_str)
            if leaves_for_day:
                days[date_cur_str]["leaves"]=leaves_for_day
                
            if not attendances and range_open:
                attendances.append( {
                    "day" : date_cur_str,
                    "from" : date_cur_str + " 00:00:00",
                    "to" : date_cur_str + " 24:00:00"
                })
            elif attendances:
                if range_open:
                    attendances[0]["from"] = date_cur_str + " 00:00:00"
                    range_open = False                        
                last_range = attendances[-1]
                if not last_range.get("to"):
                    range_open = True                    
                    last_range["to"]= util.timeToStr(date_cur+delta_day)                    
            date_cur += delta_day   
        
        #get total days
        cr.execute('SELECT day.name, day.total_attendance, day.total_timesheet, day.total_difference\
                FROM hr_timesheet_sheet_sheet AS sheet \
                LEFT JOIN hr_timesheet_sheet_sheet_day AS day \
                    ON (sheet.id = day.sheet_id \
                        AND day.name IN %s) \
                WHERE sheet.id = %s',(tuple(days.keys()),oid) )
        
        for total_day in cr.fetchall():       
            if total_day[0]:     
                days[total_day[0]]['total_attendance_day'] = total_day[1]
                days[total_day[0]]['total_timesheet_day'] = total_day[2]
                days[total_day[0]]['total_difference_day'] = total_day[3]
                
        #get analytic lines
        line_obj = self.pool.get("hr.analytic.timesheet")        
        for key,value in days.items():
            value["lines"] = line_obj.search(cr, uid, [("date","=",key),("sheet_id","=",timesheet.id)], order="id asc")            
                    
        return days
    
    _inherit = "hr_timesheet_sheet.sheet"


class hr_timesheet_line(osv.osv):
    def _amount_brutto(self, cr, uid, ids, field_name, arg, context=None):      
        tax_obj= self.pool.get("account.tax")
        res = {}        
        for line in self.browse(cr, uid, ids, context=context):
            amount = 0.0
            product = line.product_id
            if product:                
                amount_all = tax_obj.compute_all(cr,uid,product.supplier_taxes_id,product.standard_price,1,product=product.id)
                amount =  amount_all["total_included"]            
            res[line.id]=amount            
        return res 
    
    _inherit = "hr.analytic.timesheet"
    _columns = {            
        "amount_brutto" : fields.function(_amount_brutto,string="Amount (Brutto)",type="float", digits_compute=dp.get_precision("Account")),
    }
