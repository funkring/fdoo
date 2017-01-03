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

from openerp.osv import fields,osv
from openerp.addons.at_base import util
from dateutil.relativedelta import relativedelta
import time

class hr_employee(osv.osv):   
    
    def _get_contract(self, cr, uid, employee_id, date_from=None, date_to=None, context=None):
        if not date_from:
            date_from = util.currentDate()
        if not date_to:
            date_to = date_from

        contract_obj = self.pool["hr.contract"]
        
        # fetch contracts
        cr.execute("SELECT c.id FROM hr_contract c"
                   " WHERE c.employee_id = %s "
                   "   AND (c.date_start IS NULL OR (c.date_start <= %s AND (c.date_end IS NULL OR c.date_end >= %s) OR (c.date_start <= %s AND c.date_start >= %s)) )"
                   " ORDER BY c.date_start DESC ",
                   (employee_id, date_from, date_from, date_to, date_from))

        contract_ids = [r[0] for r in cr.fetchall()]
        
        # return if not found
        if not contract_ids:
            return None
        
        # validate range
        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            # check working_hours            
            if not contract.working_hours:
                continue
            
            # validate range
            if date_from < contract.date_start:
                date_from = contract.date_start
            if contract.date_end and contract.date_end < date_to:
                date_to = contract.date_end
            
            # check date_to
            if date_to < date_from:
                continue 
            
            return {
                "contract" : contract,
                "working_hours" : contract.working_hours,
                "date_from" : date_from,
                "date_to" : date_to
            }
        return None 
    
    def attendance_action_change(self, cr, uid, ids, context=None):
        if not context:
            context = {}
            
        action = context.get('action', False)
        attendance_obj = self.pool.get("hr.attendance")
        
        for employee in self.browse(cr, uid, ids, context):
            #
            if not action:
                if employee.state == "present": action = "sign_out"
                if employee.state == "absent": action = "sign_in"
            #
            if action=="sign_out":
                contract = employee.contract_id
                if contract:                    
                    break_interval = contract.break_interval
                    break_duration = contract.break_duration
                    if break_interval and break_duration and contract.break_auto:                        
                        attendance_ids = attendance_obj.search(cr,uid,[("employee_id","=",employee.id)],limit=1)                                                
                        if attendance_ids:
                            last_att = attendance_obj.browse(cr,uid,attendance_ids[0],context)
                            until_time = util.strToTime(context.get("default_name",time.strftime(util.DHM_FORMAT)))                            
                            if last_att.action == "sign_in":
                                from_time = util.strToTime(last_att.name)                                                                
                                break_interval_delta = relativedelta(hours=break_interval)
                                break_duration_delta = relativedelta(hours=break_duration)
                                next_break = from_time+break_interval_delta                                
                                while next_break < until_time:                                    
                                    att_id = attendance_obj.create(cr,uid, {
                                                    "name" : util.timeToStr(next_break),
                                                    "action" : "sign_out",
                                                    "employee_id" : employee.id
                                                }, context)
                                    
                                    # check if after break sign in would be after sign out
                                    next_break += break_duration_delta 
                                    if next_break >= until_time:
                                        return att_id
                                    
                                    att_id  = attendance_obj.create(cr,uid, {
                                                    "name" : util.timeToStr(next_break),
                                                    "action" : "sign_in",
                                                    "employee_id" : employee.id
                                                }, context)
                                    next_break += break_interval_delta                                    
                                                                        
                                        
        att_id = super(hr_employee,self).attendance_action_change(cr,uid,ids,context=context)
        return att_id
                
        
        
    _inherit = "hr.employee"    
