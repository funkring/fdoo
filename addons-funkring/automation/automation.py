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
from openerp.addons.at_base import util
from openerp import SUPERUSER_ID

class TaskStatus(object):
  def __init__(self, task):
    self.task = task
    
  def log(self, message):
    pass
  
  def loge(self, message, e):
    pass
  
  def stage(self, subject):
    pass 
  
  def start(self):
    pass

  
class automation_task(models.Model):
  _name = "automation.task"
  _description = "Automation Task"
  _order = "id asc"
  
  name = fiels.Char("Name", required=True)
  
  state_change = fields.Datetime("State Change", default=lambda self: util.currentDateTime(), required=True)
  state = fields.Selection([
      ("draft","Draft"),
      ("queued","Queued"),
      ("run","Running"),
      ("cancel","Canceled"),
      ("failed","Failed"),
      ("done","Done")
    ], required=True, index=True, default="draft")
    
  progress = fields.Float("Progress")  
  error = fields.Char("Error")
  owner_id = fields.Many2one("res.users","Owner", required=True, default=lambda self: self._uid, index=True)
  res_model = fields.Char("Resource Model", required=True, index=True)
  res_id = fields.Integer("Resource ID", required=True, index=True)
  cron_id = fields.Many2one("ir.cron","Scheduled Job", index=True, ondelete="set null")  
  stage_ids = fields.One2Many("automation.task.stage", "task_id", "Stages")

  @api.one  
  def _run(self, taskc):
    pass
  
  @api.one
  def action_queue(self):
    if task.state in ("draft", "cancel", "failed"):
      
      # new cron entry
      cron_values =  {
        "name": task,
        "user_id": SUPERUSER_ID,
        "interval_type": "minutes",
        "interval_number": 1,
        "nextcall": util.currentDateTime(),
        "numbercall": 1,
        "args": "(%s,)" % self.id,
        "active": True,
        "priority": 1000 + task.id      
      }
      
      sudo_task = task.sudo() 
      sudo_cron = sudo_task.cron_id
      if not sudo_cron:
        sudo_cron = self.env["ir.cron"].sudo().create(cron_values)
      else:
        sudo_cron.write(cron_values)
      
      sudo_task.stages_ids.active = False
      sudo_task.status = "queued"
      sudo_task.error = None
      sudo_task.cron_id = cron
        
  @api.model
  def _process_task(self, task_id):
    task = self.browse(task_id)
    if task and task.state == "queued":      
      try:
        model_obj = self.env[task.res_model]
        resource = model_obj.browse(task.res_id)
                
        # run task
        taskc = TaskStatus(task)        
        with self._cr.savepoint():
          taskc.start()
          resource._run(taskc)
                  
        task.state_change = util.currentDateTime()
        task.state = "done"
        task.error = None
      except Exception as e:
        task.state_change = util.currentDateTime()
        task.state = "failed"
        task.error = str(e)
  
  
class automation_task_stage(models.Model):
  _name = "automation.task.stage"
  _description = "Task Stage"
  
  name = fields.Char("Name")
  processed = fields.Float("Processed %")
  
  task_id = fields.Many2one("automation.task", "Task")
  parent_id = fields.Many2one("automation.task.stage", "Parent Stage")
  active = fields.Boolean("Active", default=True)
  
     
class automation_task_log(models.Model):
  _name = "automation.task.log"
  _description = "Task Log"
  _order = "id asc"
  
  task_id = fields.Many2one("automation.task", "Task", required=True)
  stage_id = fields.Many2one("automation.stage","Stage", required=True)
  
  pri = fields.Selection([("x","Emergency"),
                          ("a","Alert"),
                          ("e","Error"),
                          ("w","Warning"),
                          ("n","Notice"),
                          ("i","Info"),
                          ("d","Debug")],
                          string="Priority",
                          default="i",
                          required=True)
  
  message = fields.Text("Message")
  
  
  