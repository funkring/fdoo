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
from at_base import format
import decimal_precision as dp
from openerp.tools.translate import _

class purchase_stage_wizard(osv.osv_memory):
        
    def stage_next(self, cr, uid, ids, context=None):        
        f = format.LangFormat(cr,uid,context,dp="Purchase Price")
        purchase_line_id = context and context.get("purchase_line_id") or None
        if purchase_line_id:
            purchase_line_obj = self.pool.get("purchase.order.line")    
            purchase_line_rec = purchase_line_obj.browse(cr,uid,purchase_line_id,context=context)
            for obj in self.browse(cr, uid, ids, context):
                message = []                
                severity = obj.level_id.severity                                
                data = {
                    "level_id" : obj.level_id.id 
                }
                
                if obj.message:
                    message.append(obj.message)
                    
                message.append(_("Level changed to %s") % (obj.level_id.name,))                
                
                if purchase_line_rec.supplier_invoiced != obj.supplier_invoiced:
                    value = obj.supplier_invoiced and _("Yes") or _("No")
                    data["supplier_invoiced"]=obj.supplier_invoiced
                    message.append(_("Supplier invoice state changed to %s") % (value,))
                                    
                if purchase_line_rec.supplier_unit_price != obj.supplier_unit_price:
                    value = f.formatLang(obj.supplier_unit_price)
                    data["supplier_unit_price"]=obj.supplier_unit_price
                    message.append(_("Supplier unit price changed to %s") % (value,))
                                                        
                purchase_line_obj.write(cr,uid,purchase_line_id,data,context=context)
                purchase_line_obj.log(cr, uid, purchase_line_id, "\n".join(message), context=context,severity=severity)               
                
                if obj.delivery:
                    return purchase_line_obj.confirm_direct_delivery(cr,uid,[purchase_line_id],context)
                
        return { "type" : "ir.actions.act_window_close" }   
    
        
    def _get_next_level(self, cr, uid, context=None):
        level_obj = self.pool.get("purchase.order_level")
        purchase_line_id = context and context.get("purchase_line_id") or None        
        
        if purchase_line_id:
            purchase_line_obj = self.pool.get("purchase.order.line")             
            purchase_line = purchase_line_obj.browse(cr, uid, purchase_line_id, context)
            if purchase_line and purchase_line.level_id:
                level_ids = level_obj.search(cr,uid,[("sequence",">",purchase_line.level_id.sequence),("severity","=","0")],context=context)
                if level_ids:
                    return level_ids[0]
            
            
        level_ids = level_obj.search(cr, uid, [("severity","=","0")], limit=1,context=context)
        if level_ids:
            return level_ids[0]            
        return None
    
    
    def _get_suppplier_unit_price(self, cr, uid, context=None):            
        purchase_line_id = context and context.get("purchase_line_id") or None    
        if purchase_line_id:
            return self.pool.get("purchase.order.line").browse(cr,uid,purchase_line_id,context=context).supplier_unit_price
        return None
    
    def _get_supplier_invoiced(self, cr, uid, context=None):            
        purchase_line_id = context and context.get("purchase_line_id") or None    
        if purchase_line_id:
            return self.pool.get("purchase.order.line").browse(cr,uid,purchase_line_id,context=context).supplier_invoiced
        return None
     
    def _get_state(self, cr, uid, context=None):            
        purchase_line_id = context and context.get("purchase_line_id") or None    
        if purchase_line_id:
            return self.pool.get("purchase.order.line").browse(cr,uid,purchase_line_id,context=context).state or "draft"
        return None
    
    def _get_description(self, cr, uid, context=None):            
        purchase_line_id = context and context.get("purchase_line_id") or None    
        if purchase_line_id:
            text = []
            line = self.pool.get("purchase.order.line").browse(cr,uid,purchase_line_id,context=context)            
            f = format.LangFormat(cr,uid,context,dp="Purchase Price")             
            text.append(f.formatLang(line.product_qty) + "  " + (line.product_uom and line.product_uom.name or ""))
            if line.name:
                text.append(line.name)
            text.append("")
            if line.notes:
                text.append(line.notes)                
            return "\n".join(text)            
        return None

    
    _name="purchase.stage_wizard"
    _description="Next Purchase Stage"
    _columns = {
        "description" : fields.text("Description",readonly=True),
        "state": fields.selection([("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done"), ("cancel", "Cancelled")], "State", required=True, readonly=True),        
        "level_id" : fields.many2one("purchase.order_level","Level",required=True),
        "supplier_invoiced" : fields.boolean("Invoiced",help="Has Supplier invoiced?"),
        "supplier_unit_price" : fields.float("Supplier Unit Price",digits_compute=dp.get_precision("Purchase Price")),
        "delivery" : fields.boolean("Delivery"),
        "message" : fields.text("Message")
    }
    
    _defaults = {
        "description" : _get_description,
        "state" : _get_state,
        "level_id" : _get_next_level,
        "supplier_unit_price" : _get_suppplier_unit_price,
        "supplier_invoiced" : _get_supplier_invoiced
    }
purchase_stage_wizard()
