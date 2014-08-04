# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

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

from openerp.osv import fields,osv

class info_wizard(osv.TransientModel):
    
    def do_show(self,cr,uid,modul,action,info,active_ids=None,context=None):
        mod_obj = self.pool.get('ir.model.data')
        action_data = mod_obj.get_object_data(cr,uid,"at_base","action_info_wizard")
        result_context = {
            "forward_modul" : modul,
            "forward_actionref" : action,
            "forward_active_ids" : active_ids,            
            "default_info" : info
        }
        action_data["context"]=str(result_context)
        action_data["nodestroy"]=True
        return action_data
        
    def do_forward(self, cr, uid, ids, context=None):
        if not context:
            return True
        
        modul=context.get("forward_modul")
        actionref=context.get("forward_actionref")
        active_model=context.get("forward_active_model")
        active_ids=context.get("forward_active_ids")
        active_id=context.get("forward_active_id")
        
        if not actionref:
            return { "type" : "ir.actions.act_window_close" }
        
        mod_obj = self.pool.get('ir.model.data')
        action_data = mod_obj.get_object_data(cr,uid,modul,actionref)
        
        result_context = {}
        if active_model:
            result_context["active_model"]=active_model
        if active_ids:
            result_context["active_ids"]=active_ids
        if active_id:
            result_context["active_id"]=active_id
        
        action_data["context"]=str(result_context)             
        return action_data
        
    _description="Info Wizard"
    _name="at_base.info_wizard"
    _columns = {
        "info" : fields.text("Info",readonly=True)
    }
