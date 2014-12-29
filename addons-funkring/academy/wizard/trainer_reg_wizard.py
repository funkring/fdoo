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

class trainer_reg_wizard(models.TransientModel):
    
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
            value.update(self.onchange_sem(semester_id, semester_id)["value"])
        elif unit == "period":
            period_obj = self.pool["account.period"]
            month = util.dateToStr(datetime.today()-relativedelta(months=1))
            period_id = period_obj.search_id(self._cr, self._uid, [("date_start","<=",month),("date_stop",">=",month)])
            value["period_start_id"] = period_id
            value["period_end_id"] = period_id
            value.update(self.onchange_period(period_id, period_id)["value"])
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
        sem_start = None
        sem_end = None
        
        if sem_start_id:
            sem_start = sem_obj.browse(sem_start_id)
            value["date_start"]=sem_start.date_start
            
        if sem_end_id:
            sem_end = sem_obj.browse(sem_end_id)
            
            # check semester end
            if sem_start and sem_end.date_end <= sem_start.date_start:
                sem_end = sem_start
                value["sem_end_id"] = sem_end.id
            
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
        period_start = None
        period_end = None
        
        if period_start_id:
            period_start = period_obj.browse(period_start_id)
            value["date_start"]=period_start.date_start
            
        if period_end_id:
            period_end = period_obj.browse(period_end_id)
            
            # check if period end
            if period_start and period_end.date_stop <= period_start.date_start:
                period_end = period_start
                value["period_end_id"] = period_end.id
                
            value["date_end"]=period_end.date_stop
            
        return res
    
    @api.v7
    def action_create(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        
        report_ctx = context and dict(context) or {}
        report_ctx["date_start"]=wizard.date_start
        report_ctx["date_end"]=wizard.date_end
          
        if wizard.unit == "semester":
            if wizard.sem_start_id.id == wizard.sem_end_id.id:
                report_ctx["duration_title"]=wizard.sem_start_id.name_get()[0][1]
            else:
                report_ctx["duration_title"]="%s - %s" % (wizard.sem_start_id.name_get()[0][1],wizard.sem_end_id.name_get()[0][1])
        elif wizard.unit == "period":
            if wizard.period_start_id.id == wizard.period_end_id.id:
                report_ctx["duration_title"]=wizard.period_start_id.name_get()[0][1]
            else:
                report_ctx["duration_title"]="%s - %s" % (wizard.period_start_id.name_get()[0][1],wizard.period_end_id.name_get()[0][1])
        else:
            f = format.LangFormat(cr, uid, context)
            report_ctx["duration_title"]="%s - %s" % (f.formatLang(wizard.date_start,date=True),f.formatLang(wizard.date_end,date=True))

        
        datas = {
             "ids": util.active_ids(context,"academy.trainer"),
             "model": "academy.trainer"
        }        
        return  {
            "type": "ir.actions.report.xml",
            "report_name": "trainer.reg",
            "datas": datas,
            "context" : report_ctx
        }
    
    
    _name = "academy.trainer.reg.wizard"
    _description = "Trainer Registrations"
    
    unit = fields.Selection([("date","Date"),
                             ("semester","Semester"),
                             ("period","Invoice Period")], 
                             "Unit", 
                             required=True,
                             default="period")
    
    sem_start_id = fields.Many2one("academy.semester","Start Semester")
    sem_end_id = fields.Many2one("academy.semester","End Semester")
    
    period_start_id = fields.Many2one("account.period","Start Period")
    period_end_id = fields.Many2one("account.period","End Period")
    
    date_start = fields.Date("Start", required=True)
    date_end = fields.Date("End", required=True)
