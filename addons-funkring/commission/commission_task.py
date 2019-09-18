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

class commission_task(models.Model):
  _name = "commission.task"
  _description = "Commission Task"
  _inherits = {
    "automation.task": "task_id"
  }
  
  @api.model
  def default_get(self, fields_list):
    res = super(commission_task, self).default_get(fields_list)
    if "name" in fields_list:
      res["name"] = _("Commission %s") % util.getFirstOfLastMonth()
    return res
  
  task_id = fields.Many2one("automation.task", "Task", required=True, index=True, ondelete="cascade")
  company_id = fields.Many2one("res.company", "Company", default=lambda self: self.env["res.company"]._company_default_get("commission.task"), required=True)
  date_from = fields.Date("From", default=lambda self: util.getFirstOfLastMonth())
  date_to = fields.Date("To", default=lambda self: util.getEndOfMonth(util.getFirstOfLastMonth()))
  remove_existing = fields.Boolean("Remove Existing", default=True)
  partner_id = fields.Many2one("res.partner", "Partner")  
  commission_count = fields.Integer("Commission Count", compute="_commission_count")
  
  
  def _run_options(self):
    self.ensure_one()
    return  {
      "stages": 1,
      "singleton": True
    }
    
  @api.one
  def _commission_count(self):
    self.commission_count = self.env["commission.line"].search_count([("task_id","=",self.id)])
  
  @api.model
  @api.returns("self", lambda self: self.id)
  def create(self, vals):
    res = super(commission_task, self).create(vals)
    res.res_model = self._name
    res.res_id = res.id
    return res
  
  @api.multi
  def action_queue(self):
    return self.task_id.action_queue()
  
  @api.multi
  def action_cancel(self):
    return self.task_id.action_cancel()
  
  @api.multi
  def action_refresh(self):
    return self.task_id.action_refresh()
  
  @api.multi
  def action_reset(self):
    return self.task_id.action_reset()
  
  @api.multi
  def unlink(self):
    cr = self._cr
    ids = self.ids
    cr.execute("SELECT task_id FROM %s WHERE id IN %%s AND task_id IS NOT NULL" % self._table, (tuple(ids),))
    task_ids = [r[0] for r in cr.fetchall()]
    res = super(commission_task, self).unlink()
    self.env["automation.task"].browse(task_ids).unlink()
    return res
  
  @api.one  
  def _run(self, taskc):
    taskc.stage("Delete Existing")
    commission_obj = self.env["commission.line"]
    if self.remove_existing:
      
      # filter
      domain = [("company_id","=",self.company_id.id),("invoiced_id","=",False)]
      if self.date_from:
          domain.append(("date",">=",self.date_from))
      if self.date_to:
          domain.append(("date","<=",self.date_to))
      if self.partner_id:
          domain.append(("partner_id","=",self.partner_id.id))
      
      # search and remove old commission lines
      commissions = commission_obj.search(domain)
      commissions_count = len(commissions)
      commissions.unlink()
      taskc.log(_("Deleted %s commissions" % commissions_count))
      
    else:
      taskc.log(_("Remove existing is deactivated!"))
    
    taskc.done()
    
  @api.model  
  def _recalc_invoices(self, domain, force=False, taskc=None):
    pass
    
    
    