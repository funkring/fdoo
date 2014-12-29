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
from openerp.addons.at_base import format

from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import date

class teacher_reg_wizard(models.TransientModel):
    
    @api.multi
    def onchange_unit(self,unit):
        value = {
        }
        res = {
          "value" : value
        }
        if unit == "semester":
            reg_obj = self.pool["academy.registration"]
            semester_id = reg_obj._get_semester_id(self._cr, self._uid, self._context)
            value["sem_start_id"] = semester_id
            value["sem_end_id"] = semester_id
        elif unit == "period":
            period_obj = self.pool["account.period"]
            month = util.dateToStr(datetime.today()-relativedelta(months=1))
            period_id = period_obj.search_id(self._cr, self._uid, [("date_start","<=",month),("date_stop",">=",month)])
            value["period_start_id"] = period_id
            value["period_end_id"] = period_id
        return res
    
    @api.multi
    def onchange_sem(self, sem_start_id, sem_end_id):
        value = {
          "date_start" : None,
          "date_end" : None
        }
        res = {
          "value" : value          
        }
        sem_obj = self.env["academy.semester"]
        
        if sem_start_id:
            sem_start = sem_obj.browse(sem_start_id)
            value["date_start"]=sem_start.date_start
            
        if sem_end_id:
            sem_end = sem_obj.browse(sem_end_id)
            value["date_end"]=sem_end.date_end
            
        return res
    
    @api.multi
    def onchange_period(self, period_start_id, period_end_id):
        value = {
          "date_start" : None,
          "date_end" : None
        }
        res = {
          "value" : value          
        }
        period_obj = self.env["account.period"]
        
        if period_start_id:
            period_start = period_obj.browse(period_start_id)
            value["date_start"]=period_start.date_start
            
        if period_end_id:
            period_end = period_obj.browse(period_end_id)
            value["date_end"]=period_end.date_stop
            
        return res
    
    @api.one
    def action_create(self):
        report_ctx = dict(self._context)
        report_ctx["date_start"]=self.date_start
        report_ctx["date_end"]=self.date_end
        
        if self.unit == "semester":
            if self.sem_start_id.id == self.sem_end_id.id:
                report_ctx["duration_title"]=self.sem_start_id.name_get()[0][1]
            else:
                report_ctx["duration_title"]="%s - %s" % (self.sem_start_id.name_get()[0][1],self.sem_end_id.name_get()[0][1])
        elif self.unit == "period":
            if self.period_start_id.id == self.period_end_id.id:
                report_ctx["duration_title"]=self.period_start_id.name_get()[0][1]
            else:
                report_ctx["duration_title"]="%s - %s" % (self.period_start_id.name_get()[0][1],self.period_end_id.name_get()[0][1])
        else:
            f = format.LangFormat(self._cr, self._uid, self._context)
            report_ctx["duration_title"]="%s - %s" % (f.formatLang(self.date_start,date=True),f.formatLang(self.date_end,date=True))
        

        # prepare report
        active_ids = util.active_ids(self._context,"academy.trainer")
        datas = {
            "ids": active_ids,
            "model": "academy.trainer",
            "form": self.read()[0]
        }
        return self.pool["report"].get_action(self._cr, self._uid, active_ids, "academy.trainer.student", data=datas, context=report_ctx)        
    
    _name = "academy.teacher.reg.wizard"
    _description = "Teacher Registrations"
    _rec_name = "date_start"
    
    unit = fields.Selection([("date","Date"),
                             ("semester","Semester"),
                             ("period","Invoice Period")], 
                             "Unit", 
                             required=True,
                             default="date")
    
    sem_start_id = fields.Many2one("academy.semester","Start Semester")
    sem_end_id = fields.Many2one("academy.semester","End Semester")
    
    period_start_id = fields.Many2one("account.period","Start Period")
    period_end_id = fields.Many2one("account.period","End Period")
    
    date_start = fields.Date("Start", required=True)
    date_end = fields.Date("End", required=True)
