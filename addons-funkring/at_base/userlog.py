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
import logging

_logger = logging.getLogger(__file__)

class log_basic(osv.AbstractModel):
    _name = "log.basic"
    _description = "Basic Log"
    _columns = {        
        "severity" : fields.selection([("i","Info"),("w","Warning"),("e","Error")],"Severity",required=True),
        "name" : fields.char("Message"),
        "detail" : fields.text("Detail")
    }
    
    def log(self,cr,uid,message,detail=None,context=None):
        _logger.info(message)
        return self.create(cr, uid, { "name" : message, "severity" : "i", "detail" : detail }, context=context)
        
    def warn(self,cr,uid,message,detail=None,context=None):
        _logger.warn(message)
        return self.create(cr, uid, { "name" : message, "severity" : "w", "detail" : detail }, context=context)
        
    def error(self,cr,uid,message,detail=None,context=None):
        _logger.error(message)
        return self.create(cr, uid, { "name" : message, "severity" : "e", "detail" : detail }, context=context)
    
    _default = {
        "severity" : "i"
    }
        

class log_temp(osv.TransientModel):
    _name = "log.temp"
    _inherit = "log.basic"
    _description = "Temporary Log"
    

class log_temp_wizard(osv.TransientModel):

    def show_logs(self, cr, uid, log_ids, context=None):
        ir_obj = self.pool.get("ir.model.data")
        wizard_form_id = ir_obj.get_object_reference(cr, uid, 'at_base', 'wizard_log_temp')[1]
        log_context = dict(context)
        log_context["default_log_ids"]=log_ids
        return  {
           "name" : "Logs",
           "type": "ir.actions.act_window",
           "view_type": "form",
           "view_mode": "form",
           "res_model": "log.temp.wizard",
           "views": [(wizard_form_id, "form")],
           "view_id": wizard_form_id,
           "context" : log_context,
           "target": "new"
        }
    
    _name = "log.temp.wizard"
    _description = "Logs"
    _columns = {
        "log_ids" : fields.many2many("log.temp", string="Logs",readonly=True)
    } 