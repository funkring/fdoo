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
from openerp.exceptions import Warning
import requests
import urlparse
import uuid
import json
import time

import logging
_logger = logging.getLogger(__name__)

def _list_all_models(self):
    self._cr.execute("SELECT model, name FROM ir_model ORDER BY name")
    return self._cr.fetchall()


class TaskLogger():
  
  def __init__(self, name):    
    self.logger = logging.getLogger(name)
    self.name = name
    self._status = None
    self._progress = 0
  
  def log(self, message, pri="i", obj=None, ref=None, progress=None):
    if pri=="i":
      self.logger.info(message)
    elif pri=="e":
      self.logger.error(message)
    elif pri=="w":
      self.logger.warning(message)
    elif pri=="d":
      self.logger.debug(message)
    elif pri=="x":
      self.logger.fatal(message)      
    elif pri=="a":
      self.logger.critical(message)
    
  def loge(self, message, pri="e", **kwargs):
    self.log(message, pri=pri, **kwargs)
  
  def logw(self, message, pri="w", **kwargs):
    self.log(message, pri=pri, **kwargs)
    
  def logd(self, message, pri="d", **kwargs):
    self.log(message, pri=pri, **kwargs)
    
  def logn(self, message, pri="n", **kwargs):
    self.log(message, pri=pri, **kwargs)
    
  def loga(self, message, pri="a", **kwargs):
    self.log(message, pri=pri, **kwargs)
  
  def logx(self, message, pri="x", **kwargs):
    self.log(message, pri=pri, **kwargs)
  
  def progress(self, status, progress):
    progress = min(round(progress),100)
    if not status:
      status = "Progress"
    if self._status != status or self._progress != progress:
      self._status = status
      self._progress = progress
      self.log("%s: %s" % (self._status, self._progress))
   
  def stage(self, subject, total=None):
    self.log("= %s" % subject)
  
  def substage(self, subject, total=None):
    self.log("== %s" % subject)
  
  def done(self):
    self.progress("Done", 100.0)
      
  def close(self):
    pass


class TaskStatus(object):
    
  def __init__(self, task, total=1):
    self.task = task
    secret = self.task.env["automation.task.secret"].search([("task_id","=",task.id)])
    if not secret:
      raise Warning(_("No scecret for task %s [%s] was generated") % (self.task, self.task.id))
    else:
      secret = secret[0].secret
    
    baseurl = self.task.env["ir.config_parameter"].get_param("web.base.url")
    if not baseurl:
      raise Warning(_("Cannot determine base url"))
    
    
    # init path
    self.log_path = urlparse.urljoin(baseurl,  "http/log/%s/%s" % (task.id, secret))
    self.stage_path = urlparse.urljoin(baseurl,  "http/stage/%s/%s" % (task.id, secret))
    self.progress_path = urlparse.urljoin(baseurl,  "http/progress/%s/%s" % (task.id, secret))
    
    # setup root stage
    self.root_stage_id = self._create_stage({"name": task.name,
                                             "total": total })
    self.parent_stage_id = self.root_stage_id
    self.stage_id = self.root_stage_id
    
    # first log
    self.log(_("Started"))
    
    # stack
    self.stage_stack = []
    self.last_status = None
    
    
  def log(self, message, pri="i", obj=None, ref=None, progress=None):
    values = {
      "stage_id": self.stage_id,
      "pri": pri,
      "message": message
    }
    if progress:
      values["progress"] = progress
    if obj:
      ref = "%s,%s" % (obj._name, obj.id)
    if ref:
      values["ref"] = ref      
    res = requests.post(self.log_path, data=values)
    res.raise_for_status()
    
  def loge(self, message, pri="e", **kwargs):
    self.log(message, pri=pri, **kwargs)
  
  def logw(self, message, pri="w", **kwargs):
    self.log(message, pri=pri, **kwargs)
    
  def logd(self, message, pri="d", **kwargs):
    self.log(message, pri=pri, **kwargs)
    
  def logn(self, message, pri="n", **kwargs):
    self.log(message, pri=pri, **kwargs)
    
  def loga(self, message, pri="a", **kwargs):
    self.log(message, pri=pri, **kwargs)
  
  def logx(self, message, pri="x", **kwargs):
    self.log(message, pri=pri, **kwargs)
  
  def progress(self, status, progress):    
    values = {
      "stage_id": self.stage_id,
      "status": status,
      "progress": min(round(progress),100)
    }
    if self.last_status is None or self.last_status != values:
      self.last_status = values
      res = requests.post(self.progress_path, data=values)
      res.raise_for_status()
  
  def _create_stage(self, values):
    res = requests.post(self.stage_path, data=values)
    res.raise_for_status()
    return int(res.text)
  
  def stage(self, subject, total=None):
    values = {
      "parent_id": self.parent_stage_id,
      "name": subject
    }
    if total:
      values["total"] = total
    self.stage_stack.append((self.parent_stage_id, self.stage_id))
    self.stage_id = self._create_stage(values)
  
  def substage(self, subject, total=None):
    values = {
      "parent_id": self.stage_id,
      "name": subject
    }
    if total:
      values["total"] = total
    self.stage_stack.append((self.parent_stage_id, self.stage_id))
    self.parent_stage_id = self.stage_id
    self.stage_id = self._create_stage(values)    
  
  def done(self):
    self.progress(_("Done"), 100.0)
    if self.stage_stack:
      self.parent_stage_id, self.stage_id = self.stage_stack.pop()
      
  def close(self):
    res = requests.post(self.progress_path, data={
      "stage_id": self.root_stage_id,
      "status": _("Done"),
      "progress": 100.0
    })
    res.raise_for_status()
 
  
class automation_task(models.Model):
  _name = "automation.task"
  _description = "Automation Task"
  _order = "id asc"
  
  name = fields.Char("Name", required=True, readonly=True, states={'draft': [('readonly', False)]})
  
  state_change = fields.Datetime("State Change", default=lambda self: util.currentDateTime(), required=True, readonly=True, copy=False)
  state = fields.Selection([
      ("draft","Draft"),
      ("queued","Queued"),
      ("run","Running"),
      ("cancel","Canceled"),
      ("failed","Failed"),
      ("done","Done")
    ], required=True, index=True, readonly=True, default="draft", copy=False)
        
  progress = fields.Float("Progress", readonly=True, compute="_progress")  
  error = fields.Text("Error", readonly=True, copy=False)
  owner_id = fields.Many2one("res.users","Owner", required=True, default=lambda self: self._uid, index=True, readonly=True)
  res_model = fields.Char("Resource Model", index=True, readonly=True)
  res_id = fields.Integer("Resource ID", index=True, readonly=True)
  res_ref = fields.Reference(_list_all_models, string="Resource", compute="_res_ref", readonly=True)
  cron_id = fields.Many2one("ir.cron","Scheduled Job", index=True, ondelete="set null", copy=False, readonly=True)  
  total_logs = fields.Integer("Total Logs", compute="_total_logs")
  total_stages = fields.Integer("Total Stages", compute="_total_stages")
  total_warnings = fields.Integer("Total Warnings", compute="_total_warnings")
  
  task_id = fields.Many2one("automation.task", "Task", compute="_task_id")
  
  @api.one
  def _task_id(self):
    self.task_id = self

  @api.multi
  def _progress(self):
    res = dict.fromkeys(self.ids, 0.0)
    cr = self._cr
    
    # search stages
    cr.execute("SELECT id FROM automation_task_stage WHERE task_id IN %s AND parent_id IS NULL",
                     (tuple(self.ids),))

    # get progress    
    stage_ids = [r[0] for r in cr.fetchall()]
    for stage in self.env["automation.task.stage"].browse(stage_ids):
      res[stage.task_id.id] = stage.complete_progress
    
    # assign
    for r in self:
      r.progress = res[r.id]
      
  @api.one
  def _res_ref(self):
    if self.res_model and self.res_id:
      res = self.env[self.res_model].search_count([("id","=",self.res_id)])
      if res:      
        self.res_ref = "%s,%s" % (self.res_model, self.res_id)
      else:
        self.res_ref = None
    else:
      self.res_ref = None

  @api.multi
  def _total_logs(self):
    res = dict.fromkeys(self.ids, 0)
    cr = self._cr
    cr.execute("SELECT task_id, COUNT(*) FROM automation_task_log WHERE task_id IN %s GROUP BY 1", (tuple(self.ids),))
    for task_id, log_count in cr.fetchall():
      res[task_id] = log_count
    for r in self:
      r.total_logs = res[r.id]
      
  @api.multi
  def _total_warnings(self):
    res = dict.fromkeys(self.ids, 0)
    cr = self._cr
    cr.execute("SELECT task_id, COUNT(*) FROM automation_task_log WHERE pri IN ('a','e','w','x') AND task_id IN %s GROUP BY 1", (tuple(self.ids),))
    for task_id, log_count in cr.fetchall():
      res[task_id] = log_count
    for r in self:
      r.total_warnings = res[r.id]
  
  @api.multi
  def _total_stages(self):
    res = dict.fromkeys(self.ids, 0)
    cr = self._cr
    cr.execute("SELECT task_id, COUNT(*) FROM automation_task_stage WHERE task_id IN %s GROUP BY 1", (tuple(self.ids),))
    for task_id, stage_count in cr.fetchall():
      res[task_id] = stage_count
    for r in self:
      r.total_stages = res[r.id]

  @api.one  
  def _run(self, taskc):
    """" Test Task """
    for stage in range(1,10):
      taskc.stage("Stage %s" % stage)
      
      for proc in range(1,100,10):
        taskc.log("Processing %s" % stage)
        taskc.progress("Processing %s" % stage, proc)  
        time.sleep(1)
                
      taskc.done()
  
  @api.multi
  def _stage_count(self):
    self.ensure_one()
    return 10
  
  def _check_execution_rights(self):
    # check rights 
    if self.owner_id.id != self._uid and not self.user_has_groups("automation.group_automation_manager,base.group_system"):
      raise Warning(_("Not allowed to start task. You be the owner or an automation manager"))          
    
  @api.multi
  def action_cancel(self):
    for task in self:
      # check rights
      task._check_execution_rights()
      if task.state == "queued":
        task.state = "cancel"
    return True
        
  @api.multi
  def action_refresh(self):
    return True
  
  @api.multi
  def action_reset(self):
    return True

  @api.multi
  def _get_cron_values(self):
    self.ensure_one()
    # new cron entry
    return {
      "name": "Task: %s" % self.name,
      "user_id": SUPERUSER_ID,
      "interval_type": "minutes",
      "interval_number": 1,
      "nextcall": util.currentDateTime(),
      "numbercall": 1,
      "model": self._name,
      "function": "_process_task",
      "args": "(%s,)" % self.id,
      "active": True,
      "priority": 1000 + self.id,
      "task_id": self.id 
    }
  
  @api.multi
  def action_queue(self):

    for task in self:
      # check rights
      task._check_execution_rights()
      if task.state in ("draft", "cancel", "failed", "done"):
        # sudo task
        sudo_task = task.sudo()
        
        # add cron entry 
        sudo_cron = sudo_task.cron_id
        if not sudo_cron:
          sudo_cron = self.env["ir.cron"].sudo().create(sudo_task._get_cron_values())
        else:
          sudo_cron.write(sudo_task._get_cron_values())
        
        # set stages inactive
        self._cr.execute("DELETE FROM automation_task_stage WHERE task_id=%s",(sudo_task.id,))
        
        # set queued
        sudo_task.state = "queued"
        sudo_task.error = None
        sudo_task.cron_id = sudo_cron
        
        # create secret
        sudo_secret = self.env["automation.task.secret"].sudo()
        if not sudo_secret.search([("task_id","=",sudo_task.id)]):
          sudo_secret.create({
            "task_id": sudo_task.id
          })
        
    return True
  
  @api.model
  def _cleanup_tasks(self):
    # clean up cron tasks
    self._cr.execute("DELETE FROM ir_cron WHERE task_id IS NOT NULL AND NOT active")
    return True
        
  @api.model
  def _process_task(self, task_id):
    task = self.browse(task_id)
    if task and task.state == "queued":      
      try:
        # get options
        if task.res_model and task.res_id:
          model_obj = self.env[task.res_model]
          resource = model_obj.browse(task.res_id)
        else:
          resource = task
        
        
        # options
        
        options = {
          "stages": 1,
          "resource": resource
        }
        
        # get custom options
        
        if hasattr(resource, "_run_options"):
          res_options = getattr(resource, "_run_options")
          if callable(res_options):
            res_options = resource._run_options()
          options.update(res_options)

        stage_count = options["stages"]
        
        # check if it is a singleton task
        # if already another task run, requeue
        # don't process this task
        if options.get("singleton"):
          # cleanup 
          self._cr.execute("DELETE FROM ir_cron WHERE task_id=%s AND id!=%s AND NOT active", (task.id, task.cron_id.id))
          # check concurrent 
          self._cr.execute("SELECT MIN(id) FROM automation_task WHERE res_model=%s AND state IN ('queued','run')", (resource._model._name,))
          active_task_id = self._cr.fetchone()[0]
          if active_task_id and active_task_id < task_id:
            # requeue
            task.cron_id = self.env["ir.cron"].create(task._get_cron_values())
            return True
        
        # change task state 
        # and commit                
        task.write({
          "state_change": util.currentDateTime(),
          "state": "run",
          "error": None        
        })
        # commit after start
        self._cr.commit()
        
        # run task
        taskc = TaskStatus(task, stage_count)        
        resource._run(taskc)
          
        # close
        taskc.close()
          
        # update status
        task.write({
          "state_change": util.currentDateTime(),
          "state": "done",
          "error": None        
        })

        # commit after finish        
        self._cr.commit()
        
      except Exception as e:
        # rollback on error
        self._cr.rollback()
        _logger.exception("Task execution failed")
        
        error = None
        if hasattr(e, "message"):
          error = e.message
        
        if not error:
          error = str(e)
        
        if not error:
          error = "Unexpected error, see logs"
        
        # write error
        task.write({
          "state_change": util.currentDateTime(),
          "state": "failed",
          "error": error        
        })
        self._cr.commit()
         
    return True
  
  
class automation_task_stage(models.Model):
  _name = "automation.task.stage"
  _description = "Task Stage"
  _order = "id asc"
  _rec_name = "complete_name"
  
  complete_name = fields.Char("Name", compute="_complete_name")
  complete_progress = fields.Float("Progess %", readonly=True, compute="_complete_progress")
  
  name = fields.Char("Name", readonly=True, required=True)
  progress = fields.Float("Progress %", readonly=True)
  status = fields.Char("Status")
  
  task_id = fields.Many2one("automation.task", "Task", readonly=True, index=True, required=True, ondelete="cascade")
  parent_id = fields.Many2one("automation.task.stage", "Parent Stage", readonly=True, index=True)
  total = fields.Integer("Total", readonly=True)
  
  child_ids = fields.One2many("automation.task.stage", "parent_id", string="Substages", copy=False)
  
  @api.one
  def _complete_name(self):
    name = []
    stage = self
    while stage:
      name.append(stage.name)
      stage = stage.parent_id
    self.complete_name = " / ".join(reversed(name))
  
  @api.model
  def _calc_progress(self, stage):
    progress = stage.progress
    if progress >= 100.0:
      return progress
    
    childs = stage.child_ids
    total = max(stage.total,len(childs)) or 1
        
    for child in childs:
      progress += self._calc_progress(child) / total
    
    return min(round(progress),100.0)
    
  @api.one
  def _complete_progress(self):
    self.complete_progress = self._calc_progress(self)
    
     
class automation_task_log(models.Model):
  _name = "automation.task.log"
  _description = "Task Log"
  _order = "id asc"
  _rec_name = "create_date"
    
  task_id = fields.Many2one("automation.task", "Task", required=True, readonly=True, index=True, ondelete="cascade")
  stage_id = fields.Many2one("automation.task.stage","Stage", required=True, readonly=True, index=True, ondelete="cascade")
  
  pri = fields.Selection([("x","Emergency"),
                          ("a","Alert"),
                          ("e","Error"),
                          ("w","Warning"),
                          ("n","Notice"),
                          ("i","Info"),
                          ("d","Debug")],
                          string="Priority",
                          default="i",
                          index=True,
                          required=True, 
                          readonly=True)
  
  message = fields.Text("Message", readonly=True)
  ref = fields.Reference(_list_all_models, string="Reference", readonly=True)
  
  
class task_secret(models.Model):
  _name = "automation.task.secret"
  _rec_name = "task_id"
  
  task_id = fields.Many2one("automation.task", "Task", requird=True, ondelete="cascade", index=True)
  secret = fields.Char("Secret", required=True, default=lambda self: uuid.uuid4().hex, index=True)
  
  
  