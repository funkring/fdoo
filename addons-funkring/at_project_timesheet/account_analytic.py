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
from openerp import SUPERUSER_ID

class account_analytic_line(osv.Model):
 
  def _project_task_id(self, cr, uid, ids, field_names, arg, context=None):
    res = dict.fromkeys(ids)
    res = dict.fromkeys(ids)
    for oid in ids:
      res[oid] = {
        "project_task_id": None,
        "project_work_id": None,
        "is_project_task": False
      }

    # get tasks    
    cr.execute("SELECT ts.line_id, w.task_id, w.id FROM project_task_work w " 
               " INNER JOIN hr_analytic_timesheet ts ON ts.id = w.hr_analytic_timesheet_id "
               " WHERE ts.line_id IN %s AND w.task_id IS NOT NULL", (tuple(ids),))
    
    for r in cr.fetchall():      
      res[r[0]]["project_task_id"] = r[1]
      res[r[0]]["project_work_id"] = r[2]
      res[r[0]]["is_project_task"] = True
      
         
     # inspect lines to determine will_invoiced
    for line in self.browse(cr, SUPERUSER_ID, ids, context=context):
      # check invoiced      
      will_invoiced = False
      if line.to_invoice:
        if line.to_invoice.factor < 100.0:
          res[line.id]["will_invoiced"] = True
        else:
          res[line.id]["will_invoiced"] = False
      else:
        account = line.account_id
        # check contract invoicing
        if account.is_contract:
          if account.recurring_invoices and account.recurring_invoice_line_ids:
            res[line.id]["will_invoiced"] = True
        # check if sale order exist
        # if exist and it is a project task
        # than will_invoiced is true
        elif account.order_id and res[line.id]["is_project_task"]:
          res[line.id]["will_invoiced"] = True
      
    return res
  
  _inherit = "account.analytic.line"
  _columns = {    
    "project_task_id": fields.function(_project_task_id, type="many2one", obj="project.task",  string="Task", radonly=True, multi="_project_task_id"),
    "project_work_id": fields.function(_project_task_id, type="many2one", obj="project.task.work",  string="Project Task Work", radonly=True, multi="_project_task_id"),
    "is_project_task": fields.function(_project_task_id, type="boolean", string="Task", radonly=True, multi="_project_task_id"),
    "will_invoiced": fields.function(_project_task_id, type="boolean", string="Will be invoiced", radonly=True, multi="_project_task_id")
  }