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

from openerp.osv import fields, osv

class account_analytic_line(osv.Model):
 
  def _project_task_id(self, cr, uid, ids, field_names, arg, context=None):
    res = dict.fromkeys(ids)
    for oid in ids:
      res[oid] = {
        "project_task_id": None,
        "project_work_id": None,
        "is_project_task": False
      }
    
    cr.execute("SELECT ts.line_id, w.task_id, w.id FROM project_task_work w " 
               " INNER JOIN hr_analytic_timesheet ts ON ts.id = w.hr_analytic_timesheet_id "
               " WHERE ts.line_id IN %s AND w.task_id IS NOT NULL", (tuple(ids),))
    
    for r in cr.fetchall():      
      res[r[0]]["project_task_id"] = r[1]
      res[r[0]]["project_work_id"] = r[2]
      res[r[0]]["is_project_task"] = True
    return res
  
  _inherit = "account.analytic.line"
  _columns = {    
    "project_task_id": fields.function(_project_task_id, type="many2one", obj="project.task",  string="Task", radonly=True, multi="_project_task_id"),
    "project_work_id": fields.function(_project_task_id, type="many2one", obj="project.task.work",  string="Project Task Work", radonly=True, multi="_project_task_id"),
    "is_project_task": fields.function(_project_task_id, type="boolean", string="Task", radonly=True, multi="_project_task_id")
  }