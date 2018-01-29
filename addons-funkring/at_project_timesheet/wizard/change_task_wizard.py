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

from openerp import models, fields, api, _
from openerp import SUPERUSER_ID

class ChangeTaskWizard(models.TransientModel):
  _name = "at_project_timesheet.change_task_wizard"
  _description = "Change Task Wizard"
  
  name = fields.Char("Name", required=True)
  line_id = fields.Many2one("hr.analytic.timesheet", "Line", ondelete="set null")  
  project_id = fields.Many2one("project.project", "Project", required=True)
  task_id = fields.Many2one("project.task", "Task", required=True)
    
  @api.model
  def default_get(self, fields_list):
    res = super(ChangeTaskWizard, self).default_get(fields_list)
    
    active_id = self._context.get("active_id")
    active_model = self._context.get("active_model")
    
    if active_id and active_model == "hr.analytic.timesheet":
      
      line = self.env["hr.analytic.timesheet"].browse(active_id)
      if line:
        name = line.name
        
        # get work
        work = line.project_work_id
        if work:
          name = work.name
            
          # get task
          task = work.task_id
          if task and "task_id" in fields_list:
            res["task_id"] = task.id
          
          # get project
          project = task.project_id
          if project and "project_id" in fields_list:
            res["project_id"] = project.id
            
        # update name
        if "name" in fields_list:
          res["name"] = name
          
        # update line
        if "line_id" in fields_list:
          res["line_id"] = line.id
        
    return res
  
  @api.multi
  def onchange_project(self, project_id, task_id):
    values = {"task_id": None}
    res = {"value": values}
    if project_id:
      project = self.env["project.project"].browse(project_id)
      task_obj = self.env["project.task"]
      if task_id:
        task = task_obj.browse(task_id)
        if task:
          if task.project_id.id != project.id:
            tasks = task_obj.search([("project_id","=",project.id),("name","=",task.name)], limit=1)
            if not tasks:
              tasks = task_obj.search([("project_id","=",project.id)], limit=1)
            if tasks:
              values["task_id"] = tasks[0].id
          else:
            values["task_id"] = task.id
      else:
        tasks = task_obj.search([("project_id","=",project.id)], limit=1)
        if tasks:
          values["task_id"] = tasks[0].id
        
    return res
  
  @api.multi
  def action_change(self):
    for wizard in self:      
      # work values
      line = wizard.line_id
      work = line.project_work_id
      if work:
        old_task = work.task_id
      
      work_values = {
          "name": wizard.name, 
          "date": line.date,
          "hours": line.unit_amount,
          "user_id": line.user_id.id,
          "task_id": wizard.task_id.id
      }
      
      # update project      
      line.account_id = wizard.project_id.analytic_account_id.id
      
      # check if work exist
      if line.project_work_id:
        # update basic       
        line.project_work_id.task_id = wizard.task_id.id
        # update values      
        line.project_work_id.write(work_values)        
      else:
        # create work
        work_values["hr_analytic_timesheet_id"] = line.id
        work = self.env["project.task.work"].with_context(no_analytic_entry=True).create(work_values)
        # write for update
        work.write(work_values)
        
      # update time, to trigger recalc   
      wizard.task_id.write({"planned_hours": wizard.task_id.planned_hours})
      if old_task and old_task.id != wizard.task_id.id:
        old_task.write({"planned_hours": old_task.planned_hours})
        
    return True
  
  @api.multi
  def action_delete(self):
    for wizard in self:
      if wizard.line_id.project_work_id:
        wizard.line_id.project_work_id.unlink()                
    return {
      'type': 'ir.actions.client',
      'tag': 'reload' 
    }
      
       