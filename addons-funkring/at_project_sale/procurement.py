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

class procurement_order(osv.Model):
    _inherit = "procurement.order"
    
    def _convert_qty_company_hours(self, cr, uid, procurement, context=None):
      # use method from sale sale 
      # line
      sale_line = procurement.sale_line_id
      if sale_line:
        self.pool["sale.order.line"]._convert_qty_company_hours(cr, uid, sale_line, context=context)
      else:
        # if no sale line 
        # use default method, but check planned hours        
        product = procurement.product_id
        if product.planned_hours:
          return product.planned_hours
        return super(procurement_order, self)._convert_qty_company_hours(cr, uid, procurement, context=context)

    def _is_procurement_task(self, cr, uid, procurement, context=None):      
      is_procurement_task = super(procurement_order, self)._is_procurement_task(cr, uid, procurement, context=context)
      if is_procurement_task:
        sale_line = procurement.sale_line_id
        if sale_line and sale_line.is_contract:
          return False
      return is_procurement_task
    
    def _create_service_task(self, cr, uid, procurement, context=None):
        sale_line = procurement.sale_line_id or None
        task_obj = self.pool["project.task"]
        sale_line_obj = self.pool["sale.order.line"]
        
        task_update = None
        
        if sale_line:
          task_update = sale_line_obj._prepare_task(cr, uid, sale_line, context=context)
          task = sale_line.pre_task_id
          # update task only, if it already exist
          if task:
            # task update
            task_update["procurement_id"] = procurement.id
            
            # set deadline
            if sale_line.task_deadline:
              task_update["date_deadline"] = sale_line.task_deadline      
              
            task_obj.write(cr, uid, task.id, task_update, context=context)
            self.write(cr, uid, [procurement.id], {'task_id': task.id}, context=context)
            self.project_task_create_note(cr, uid, [procurement.id], context=context)
            return task.id
        
        task_id = super(procurement_order, self)._create_service_task(cr, uid, procurement, context=context)
        # update created task in respect of sale line entries
        if task_update:
          task_obj.write(cr, uid,task_id, task_update, context=context)
        return task_id
