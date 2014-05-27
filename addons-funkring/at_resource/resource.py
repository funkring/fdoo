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
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import math


class resource_calendar(osv.osv):
          
    def get_leave_intervals(self, cr, uid, oid, resource_id=None,
                            start_datetime=None, end_datetime=None,
                            context=None):
        """Get the leaves of the calendar. Leaves can be filtered on the resource,
        the start datetime or the end datetime.

        :param int resource_id: the id of the resource to take into account when
                                computing the leaves. If not set, only general
                                leaves are computed. If set, generic and
                                specific leaves are computed.
        :param datetime start_datetime: if provided, do not take into account leaves
                                        ending before this date.
        :param datetime end_datetime: if provided, do not take into account leaves
                                        beginning after this date.

        :return list leaves: list of tuples (start_datetime, end_datetime) of
                             leave intervals
        """
        resource_cal_leaves = self.pool.get('resource.calendar.leaves')
        dt_leave = []

        query = "SELECT id FROM resource_calendar_leaves AS l WHERE l.calendar_id=%s " % (str(oid),)
        if resource_id:
            query += " AND ( l.resource_id IS NULL OR l.resource_id = %s )" % (str(resource_id),)
        else:
            query += " AND l.resource_id IS NULL "
        if start_datetime and end_datetime:
            query += " AND (DATE '%s', DATE '%s') OVERLAPS (l.date_from,l.date_to) " % (util.dateToStr(start_datetime),util.dateToStr(end_datetime))
        elif start_datetime:
            query += " AND l.date_to >= DATE '%s'" % (util.dateToStr(start_datetime),)
        elif end_datetime:
            query += " AND l.date_from <= DATE '%s' " % (util.dateToStr(end_datetime),)            
        query += " ORDER BY l.date_from "
        
        cr.execute(query)
        resource_leave_ids = [row[0] for row in cr.fetchall()]
        
        res_leaves = resource_cal_leaves.browse(cr, uid, resource_leave_ids, context=context)
        for leave in res_leaves:
            dtf = util.strToTime(leave.date_from) 
            dtt = util.strToTime(leave.date_to) 
            no = dtt - dtf
            [dt_leave.append(util.dateToStr(dtf + timedelta(days=x))) for x in range(int(no.days + 1))]
            dt_leave.sort()

        return dt_leave
    
    def working_day_count(self,cr,uid,sid,dt_from,dt_to,resource=False,context=None):        
        if not sid:
            return 0
        
        dt_from = util.timeToDate(dt_from)
        dt_to = util.timeToDate(dt_to)
        
        attent_obj = self.pool.get("resource.calendar.attendance") 
        leaves = self.get_leave_intervals(cr, uid, sid, resource,dt_from,dt_to,context=context)            
        step = relativedelta(days=1)          
        working_days = 0

        while (dt_from <= dt_to):
            cur_date = util.dateToStr(dt_from)            
            if not cur_date in leaves:
                attent_count = attent_obj.search_count(cr,uid,[('dayofweek','=',str(dt_from.weekday())),('calendar_id','=',sid)])                
                if attent_count:
                    working_days += 1               
            dt_from +=  step
        return working_days
    
    
    def nonworking_day_count(self,cr,uid,sid,dt_from,dt_to,resource=False,context=None):
        if not sid:
            return 0
        
        dt_from = util.timeToDate(dt_from)
        dt_to = util.timeToDate(dt_to)
        
        attent_obj = self.pool.get("resource.calendar.attendance") 
        leaves = self.get_leave_intervals(cr, uid, sid, resource,dt_from,dt_to,context=context)         
        step = relativedelta(days=1)          
        non_working_days = 0

        while (dt_from <= dt_to):
            cur_date = util.dateToStr(dt_from)            
            if not cur_date in leaves:
                attent_count = attent_obj.search_count(cr,uid,[('dayofweek','=',str(dt_from.weekday())),('calendar_id','=',sid)])                
                if not attent_count:
                    non_working_days += 1    
            else:
                non_working_days += 1           
            dt_from +=  step
        return non_working_days
                
    def passed_range(self, cr, uid, oid, dt_from ,working_days, resource=False, context=None):
        if not oid:
            return None
        
        dt_cur = util.timeToDate(dt_from)
        step = relativedelta(days=1)
        
        attent_obj = self.pool.get("resource.calendar.attendance")
        leaves =  self.get_leave_intervals(cr, uid, oid, resource, dt_from, context=context)            
                
        res_dt_from = None
        res_dt_to = None
        iter_watchdog = 0
        days_left = working_days
        
        while (days_left > 0):
            cur_date = util.dateToStr(dt_cur)            
            if not cur_date in leaves:
                attent_ids = attent_obj.search(cr,uid,[('dayofweek','=',str(dt_cur.weekday())),('calendar_id','=',oid)])                
                if attent_ids:                                                           
                    dt_first = None
                    dt_last = None
                                        
                    for attent in attent_obj.browse(cr,uid,attent_ids):
                        dt_attent_from = dt_cur+relativedelta(hours=attent.hour_from)
                        dt_attent_until = dt_cur+relativedelta(hours=attent.hour_to)    
                        if not dt_first or dt_first > dt_attent_from:                                      
                            dt_first = dt_attent_from
                        if not dt_last or dt_last < dt_attent_until:
                            dt_last = dt_attent_until
                    
                    if dt_from <= dt_first:
                        iter_watchdog=0
                        days_left-=1
                        if not res_dt_from:
                            res_dt_from = dt_first                    
                    res_dt_to = dt_attent_until
                    
                elif iter_watchdog > 7: #no days found
                    break
                
                iter_watchdog+=1                                                
            dt_cur +=  step            
        
        res = None    
        if res_dt_from and res_dt_to:
            res =  {
                "from" : res_dt_from,
                "to" : res_dt_to
            }
        elif res_dt_from:
            res =  {
                "from" : res_dt_from,
                "to" : res_dt_from+relativedelta(days=working_days)         
            }
        else:
            res = {
                "from" : dt_from,
                "to" : dt_from+relativedelta(days=working_days)
            }                    
        return res

    def interval_hours_without_leaves(self, cr, uid, sid, dt_from, dt_to, resource=False, context=None):
        if not sid:
            return 0.0
        
        leaves = self.get_leave_intervals(cr, uid, sid, resource, dt_from, dt_to, context=None)
        hours = 0.0     
        step = relativedelta(days=1)          

        while (dt_from <= dt_to):
            cur_date = util.dateToStr(dt_from)            
            if not cur_date in leaves:
                cr.execute("SELECT hour_from,hour_to FROM resource_calendar_attendance WHERE dayofweek='%s' and calendar_id=%s ORDER BY hour_from", (dt_from.weekday(),sid))
                der =  cr.fetchall()            
                for (hour_from,hour_to) in der:
                    hours += math.fabs(hour_to-hour_from)                                    
            dt_from +=  step
        return hours
    
    _inherit = "resource.calendar"


class resource_calendar_attendance(osv.osv):
        
    def _hours_inv(self,cr,uid,ids, name, value, arg, context=None):
        res = self.read(cr, uid, ids, ["hour_from"], context)
        hour_from = res.get("hour_from",0.0)        
        self.write(cr, uid, ids, { "hour_to" : hour_from+value } , context)
        return True
    
    def _hours(self, cr, uid, ids, field_name, arg, context=None):
        res = {}        
        for obj in self.browse(cr, uid, ids, context=context):            
            if obj.hour_from and obj.hour_to:
                res[obj.id]=math.fabs(obj.hour_to-obj.hour_from)
            else:
                res[obj.id]=0.0                
        return res
        
    def onchange_hours(self, cr, uid, ids, hour_from, hour_to, hours=0.0, context=None):
        if hours and hour_from:
            return {"value" : { "hour_to" : hour_from+hours }}
        else:
            if not hour_to:
                return {"value" : { "hours": 0.0 } }
            else:
                return {"value" : { "hours": math.fabs(hour_to-hour_from) }}
        
        
    _inherit = "resource.calendar.attendance"
    _columns = {        
        "hours" : fields.function(_hours,fnct_inv=_hours_inv,string="Hours",required=True,readonly=False)
    }
