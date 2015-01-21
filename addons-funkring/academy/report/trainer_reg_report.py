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

from openerp.addons.at_base import util
from openerp.addons.at_base import extreport
from openerp.tools.translate import _
from datetime import datetime
from openerp.addons.at_base import util

class Parser(extreport.basic_parser):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        
        date_start = context.get("date_start")
        date_end = context.get("date_end")
        duration_title = context.get("duration_title","")
        
        if not date_start or not date_end:
            reg_obj = self.pool["academy.registration"]
            sem_obj = self.pool["academy.semester"]
            semester = sem_obj.browse(cr, uid, reg_obj._get_semester_id(cr, uid, context=context), context=context)
            date_start = semester.date_start
            date_end = semester.date_end
            if not duration_title:            
                duration_title = semester.name_get()[0][1]
            
        
        self.localcontext.update({
           "date_start" :  date_start,
           "date_end" : date_end,
           "duration_title" : duration_title,
           "students" : self._students,
           "minutes" : self._minutes,
           "start_date" : self._start_date,
           "start_date_format" : _("%d.%m.%Y KW %W")
        })
        
    def _minutes(self, reg_data):
        return int(reg_data["hours"]*60.0)
    
    def _start_date(self, reg_data):
        start_date = util.strToDate(reg_data["start_date"])
        return datetime.strftime(start_date, self.localcontext["start_date_format"])
        
    def _students(self, trainer):
        trainer_obj = self.pool["academy.trainer"]
        trainer_regs = trainer_obj._students(self.cr, self.uid, [trainer.id], 
                              self.localcontext["date_start"], 
                              self.localcontext["date_end"], 
                              context=self.localcontext)[0]["regs"].values()
             
        trainer_regs = sorted(trainer_regs, key=lambda trainer_reg: trainer_reg["reg"].student_id.name)
        minutes = 0.0
        hours = 0.0
        for reg_data in trainer_regs:
            minutes += self._minutes(reg_data)
            hours += reg_data["hours"]
        
        return [{
            "regs" : trainer_regs,
            "minutes" : int(minutes),
            "hours" : hours
        }]
        