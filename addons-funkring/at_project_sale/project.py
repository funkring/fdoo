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

from openerp.osv import fields,osv
from openerp.addons.at_base import util

class project_work(osv.osv):

    def onchange_user(self, cr, uid, ids, date, hours, user_id):        
        if uid==user_id:
            ts_obj = self.pool.get("hr_timesheet_sheet.sheet")
            ts_day = ts_obj.get_timesheet_day(cr,uid,util.currentDate())
            if ts_day:
                return {"value" : {"hours" : ts_day.total_difference }}    
        return {}
       
    _inherit = "project.task.work"   


class project_task(osv.osv):
       
    def _invoice_hours_get(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids,0.0)
        proc_obj = self.pool.get("procurement.order")
        for obj in self.browse(cr, uid, ids, context):
            proc = obj.procurement_id
            if proc:
                res[obj.id]=proc_obj.quantity_get(cr,uid,proc.id,context=context)        
        return res
    
    def _invoice_hours_set(self, cr, uid, oid, field_name, field_value, arg, context=None):
        obj = self.browse(cr, uid, oid, context)
        proc_obj = self.pool.get("procurement.order")
        sale_line_obj = self.pool.get("sale.order.line")
        proc = obj.procurement_id
        if proc:
            proc_obj.write(cr,uid,proc.id,{"product_qty" : field_value },context)                                              
            sale_line_ids = sale_line_obj.search(cr,uid,[("procurement_id","=",proc.id)])
            if len(sale_line_ids)==1 :
                sale_line = sale_line_obj.browse(cr,uid,sale_line_ids[0],context)
                if sale_line.state in ("draft","confirmed"):
                    sale_line_obj.write(cr,uid,sale_line.id,{"product_uom_qty" : field_value },context)
                    sale_line_obj.write(cr,uid,sale_line.id,{"product_uos_qty" : field_value },context)
                        
    def _order_based_invoice(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids,False)
        for obj in self.browse(cr, uid, ids, context):
            if obj.procurement_id:
                res[obj.id]=True        
        return res
    
    _columns = {
        "invoice_hours" : fields.function(_invoice_hours_get, fnct_inv=_invoice_hours_set, type="float",string="Hours to Invoice"),
        "order_based_invoice" : fields.function(_order_based_invoice,type="boolean",string="Invoice based on Order")
    }    
    _inherit = "project.task"
      
