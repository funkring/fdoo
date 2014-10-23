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
from openerp.addons.at_base import util
from openerp.tools.translate import _

class working_report_wizard(osv.TransientModel):
    
    def action_working_report(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        line_obj = self.pool["account.analytic.line"]
        act_obj = self.pool.get('ir.actions.act_window')
        line_ids = util.active_ids(context,"account.analytic.line")       
        
        values = {
            "description" : wizard.description,
            "analytic_line_ids" : [(6,0,line_ids)]
        }
        
                
        working_report_obj = self.pool["working.report"]
        report_id = working_report_obj.create(cr, uid, values, context=context)
        
        action = act_obj.for_xml_id(cr, uid, "working_report", "action_working_report", context=context)
        if not action:
            return { "type" : "ir.actions.act_window_close" }
        
        action["domain"] = "[('id','in',[%s])]" % report_id
        return action
        
    
    
    _name = "working.report.wizard"
    _description = "Working Report Wizard"
    _columns = {
        "description" : fields.text("Description")
    }