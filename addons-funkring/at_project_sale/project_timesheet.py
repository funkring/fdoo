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

from openerp.osv import osv
from at_base import util

class project_work(osv.osv):
    
    def onchange_user(self, cr, uid, ids, date, hours, user_id):        
        if uid==user_id:
            ts_obj = self.pool.get("hr_timesheet_sheet.sheet")
            ts_day = ts_obj.get_timesheet_day(cr,uid,util.currentDate())
            if ts_day:
                return {"value" : {"hours" : ts_day.total_difference }}    
        return {}
       
    
    _inherit = "project.task.work"   
