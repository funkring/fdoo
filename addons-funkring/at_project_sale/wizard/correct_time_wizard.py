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

from openerp.osv import osv,fields

class correct_time_wizard(osv.osv_memory):
    
    def _sale_line_get(self,cr,uid,task,context):
        #correct procurement
        procurement = task.procurement_id
        if procurement:
            sale_line_obj = self.pool.get("sale.order.line")                                   
            sale_line_ids = sale_line_obj.search(cr,uid,[("procurement_id","=",procurement.id)])
            if len(sale_line_ids)==1 :
                sale_line = sale_line_obj.browse(cr,uid,sale_line_ids[0],context)
                if sale_line.state in ("draft","confirmed"):
                    return sale_line                
        return None
                   
    
    def default_get(self, cr, uid, fields_list, context=None):                    
        res = {}
        active_id = context and context.get("active_id") or None
        if active_id:
            task_obj = self.pool.get("project.task")
                         
            task = task_obj.browse(cr,uid,active_id,context)
            res["task_id"]=task.id
            res["planned_hours"]=task.planned_hours
            
            sale_line=self._sale_line_get(cr, uid, task, context)
            if sale_line:
                res["offered_hours"]=sale_line.product_uom_qty
                res["correct_offered_hours"]=True
            else:
                res["offered_hours"]=0.0
                res["correct_offered_hours"]=False            
        
        return res
      
            
    def do_correction(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids,context=context):
            task = obj.task_id
            if task and task.state != "done":
                #correct task                
                task_obj = self.pool.get("project.task")                         
                task_obj.write(cr,uid,task.id,{"planned_hours" : obj.task_hours},context)
                
                #correct sale line
                if obj.correct_offered_hours:
                    sale_line_obj = self.pool.get("sale.order.line")
                    sale_line = self._sale_line_get(cr, uid, task, context)
                    if sale_line:
                        sale_line_obj.write(cr,uid,sale_line.id,{"product_uom_qty" : obj.task_hours },context)
                        sale_line_obj.write(cr,uid,sale_line.id,{"product_uos_qty" : obj.task_hours },context)
                        
        return { "type" : "ir.actions.act_window_close" }
        
        
    _name = "at_project_sale.correct_time_wizard"
    _columns = {
        "task_id" : fields.many2one("project.task","Task"),
        "task_hours" : fields.float("Task Hours Correction"),
        "planned_hours" : fields.float("Planned Hours",readonly=True),
        "offered_hours" : fields.float("Offered Hours",readonly=True),
        "correct_offered_hours" : fields.boolean("Correct offered Hours")
    }  