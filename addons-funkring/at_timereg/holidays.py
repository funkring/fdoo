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

from openerp.osv import osv,fields
from itertools import groupby
from operator import itemgetter

class hr_holidays_status(osv.osv):
    
    def get_days_sum(self, cr, uid, ids, employee_id, return_false, context=None):
        if ids:        
            cr.execute("SELECT id, type, number_of_days, holiday_status_id FROM hr_holidays WHERE employee_id = %s AND state='validate' AND holiday_status_id in %s",
                [employee_id, tuple(ids)])
            result = sorted(cr.dictfetchall(), key=lambda x: x['holiday_status_id'])
            grouped_lines = dict((k, [v for v in itr]) for k, itr in groupby(result, itemgetter('holiday_status_id')))
            res = {}
            max_leaves = 0
            leaves_taken = 0        
            for record in self.browse(cr, uid, ids, context=context):
                res[record.id] = {}            
                if record.id in grouped_lines:
                    leaves_taken = leaves_taken + sum([item['number_of_days'] for item in grouped_lines[record.id] if item['type'] == 'remove'])
                    max_leaves = max_leaves + sum([item['number_of_days'] for item in grouped_lines[record.id] if item['type'] == 'add'])
                    
            remaining_leaves = max_leaves + leaves_taken
            return {
               "max_leaves" : max_leaves,
               "leaves_taken" : -leaves_taken,
               "remaining_leaves" : remaining_leaves
            }
        else:
            return {
               "max_leaves" : 0,
               "leaves_taken" : 0,
               "remaining_leaves" : 0
            }
        
    
    _inherit = "hr.holidays.status"


class hr_holidays(osv.osv):

    def holidays_validate(self, cr, uid, ids, context=None):
        """ Add Resource Leaves """
        if super(hr_holidays,self).holidays_validate(cr, uid, ids, context=context):
            data_holiday = self.browse(cr, uid, ids,context=context)
            obj_res_leave = self.pool.get('resource.calendar.leaves')        
            for record in data_holiday:
                working_hours = record.employee_id.working_hours
                if working_hours:                
                    if record.holiday_type == 'employee' and record.type == 'remove':
                        vals = {
                           'name' : record.name,
                           'calendar_id' : working_hours.id,
                           'resource_id' : record.employee_id.resource_id.id,
                           'date_from' : record.date_from,
                           'date_to' : record.date_to,
                           'holiday_id': record.id                 
                        }
                        leave_id = obj_res_leave.create(cr,uid,vals)                      
                        self.write(cr, uid, ids, {'leave_id': leave_id})
            return True
        return False
  
    def holidays_cancel(self, cr, uid, ids, context=None):
        """ Remove Resource Leaves """
        if super(hr_holidays,self).holidays_cancel(cr,uid,ids,context=context):
            obj_res_leave = self.pool.get('resource.calendar.leaves')
            for record in self.browse(cr, uid, ids):
                if record.leave_id:
                    obj_res_leave.unlink(cr,uid,[record.leave_id.id])
            return True
        return False

    def holidays_reset(self, cr, uid, ids, context=None):
        #Bugfix: Transition from validated to draft is not handled correctly
        for record in self.browse(cr, uid, ids):
            if record.state == "validate":
                self.holidays_cancel(cr, uid, ids)
        return super(hr_holidays,self).holidays_reset(cr,uid,ids,context=context)
    
    _inherit = "hr.holidays"
    _columns = {
        "leave_id" : fields.many2one("resource.calendar.leaves","Leave Resource")
    }        

