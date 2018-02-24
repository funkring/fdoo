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
        if sale_line:
          task_obj = self.pool["project.task"]
          task = sale_line.pre_task_id
          
          # update task only, if it already exist
          if task:
            task_obj.write(cr, uid, task.id, {
              "procurement_id": procurement.id
            })
            self.write(cr, uid, [procurement.id], {'task_id': task.id}, context=context)
            self.project_task_create_note(cr, uid, [procurement.id], context=context)
            return task.id
        
        return super(procurement_order, self)._create_service_task(cr, uid, procurement, context=context)
