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

from openerp.osv import osv, fields
from openerp.tools.translate import _
import netsvc

class purchase_order_line(osv.osv):
    
    def _has_update(self, cr, uid, ids, field_names, arg, context=None):
        res = dict.fromkeys(ids,False)
                
        cr.execute("SELECT l.id,l.partner_id,u1.partner_id,u2.partner_id " 
                   " FROM purchase_order_line AS l " 
                   " LEFT JOIN res_users AS u1 ON u1.id = l.create_uid "
                   " LEFT JOIN res_users AS u2 ON u2.id = l.write_uid "
                   " WHERE l.id IN %s ", (tuple(ids),) )
                        
        for row in cr.fetchall():
            line_id = row[0]
            partner_id = row[1]
            chg_partner_id = row[3] or row[2] or None
            res[line_id]=chg_partner_id != partner_id
            
        return res
    
    def confirm(self,cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for obj in self.browse(cr, uid, ids, context):
            if obj.order_id.state == 'draft':                
                wf_service.trg_validate(uid, "purchase.order", obj.order_id.id, "purchase_confirm", cr)
        return True
    
    def is_print_for_customer(self,cr,uid,line,context=None):
        return line.supplier_ships
    
    def print_picking(self,cr,uid,ids,context=None):
        print_context = context and context.copy() or {}
        return {            
            "type": "ir.actions.report.xml",
            "report_name": "stock.picking.list_small",
            "datas": {"ids": ids, "model":"purchase.order.line"},
            "context" : print_context
        }    
    
    def dummy(self,cr,uid,ids,context=None):
        return True
    
    def show_info(self,cr, uid, ids, context=None):
        res_obj = self.pool.get("ir.model.data")
        view_id = res_obj.get_object_reference(cr,uid,"supplier_area","form_purchase_line")[1]
        return {
            "name" : _("Order Line"),
            "view_type" : "form",
            "view_mode" : "form",
            "res_model" : "purchase.order.line",
            "type" : "ir.actions.act_window",
            "view_id" : False,
            "views" : [(view_id,"form")],
            "res_id" : ids[0],
            "target" : "new",
            "nodestroy": True
        }       
    
    def stage_next(self, cr, uid, ids, context=None):        
        return {
            "name" : _("Next Stage"),
            "view_type" : "form",
            "view_mode" : "form",
            "res_model" : "purchase.stage_wizard",
            "type" : "ir.actions.act_window",
            "context" : {"purchase_line_id" : ids[0] },
            "target" : "new",
            "nodestroy": True
        }       
    
    def open_attachments(self, cr, uid, ids, context=None):        
        for obj in self.browse(cr, uid, ids, context):
            attachment_obj = self.pool.get("ir.attachment")
            url = attachment_obj.external_res_url(cr,uid,self._name,obj.id,context=context)
            if url:
                return {                   
                   "type": "ir.actions.act_url",    
                   "url" : url,
                   "target" : "new",
                   "nodestroy": True
                }                            
        return False
    
        
    _inherit = "purchase.order.line"
    _columns = {
        "supplier_update" : fields.function(_has_update,string="Supplier Update", type="boolean",store=True)    
    }
purchase_order_line()