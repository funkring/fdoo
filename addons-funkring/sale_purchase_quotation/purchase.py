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
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)

class purchase_order_line(osv.osv):
    
    def _get_pricelist_price(self, cr, uid, ids, field_name=None, arg=None, context=None):
        """Get price by analyzing the pricelist of the given supplier."""
        res = dict.fromkeys(ids)
        pricelist_obj = self.pool.get("product.pricelist")
        
        for line in self.browse(cr, uid, ids, context=context):
            partner = line.partner_id
            pricelist = partner.property_product_pricelist_purchase
            product = line.product_id
            
            if not product or not pricelist or not partner:
                continue
            
            res[line.id] = product.standard_price
            
            if pricelist:
                price_dict = pricelist_obj.price_get(cr, uid, [pricelist.id], product.id, line.product_qty, context=context)
                if price_dict:
                    price = price_dict[pricelist.id]
                    if price:
                        res[line.id] = price
                        
        return res
    
#     def onchange_quotation_price(self, cr, uid, ids, price, context=None):
#         if ids:
#             for line in self.browse(cr, uid, ids, context):
#                 if not line.order_id.state in ("confirmed","approved","done"):                
#                     self.write(cr, uid, line.id, {"price" : price}, context=context)
#         return {"value" : {}}
    
    def _send_supplier_mail(self, cr, uid, ids, context=None):
        if not ids:
            return True
        
        model_obj = self.pool["ir.model.data"]
        
        # get template
        try:
            template_id = model_obj.get_object_reference(cr, uid, "sale_purchase_quotation", "email_purchase_quotation")[1]
        except ValueError:
            _logger.warn("Mail Template 'sale_purchase_quotation.email_to_supplier_with_quotation' not found")
            template_id = False
            
        # get compose form
#         try:
#             compose_form_id = model_obj.get_object_reference(cr, uid, "mail", "email_compose_message_wizard_inherit_form")[1]
#         except ValueError:
#             _logger.warn("Compose form 'mail_template.email_compose_message_wizard_inherit_form' not found")
        compose_form_id = False 
        
        except_supplier_mail_sent = context and context.get("except_supplier_mail_sent") or False
        composition_mode = len(ids) > 1 and "mass_mail" or "comment"
        
        purchase_ids = []        
        for line in self.browse(cr, uid, ids, context):

            # check mail send
            if line.quot_sent:
                if except_supplier_mail_sent:
                    raise osv.except_osv(_('Warning!'), _('E-mail was already sent to this supplier!'))
                else:
                    continue
            
            # add order for mail
            purchase_order = line.order_id
            if not purchase_order.id in purchase_ids:
                purchase_ids.append(purchase_order.id)
            
        if not purchase_ids:
            return True
        
        email_context = {
            "active_ids" : purchase_ids,
            "active_id" : purchase_ids[0],
            "active_model" : "purchase.order",
            "context_origin" : "_send_supplier_mail",
            "default_model" : "purchase.order",
            "default_res_id" : purchase_ids[0],
            "default_composition_mode" : composition_mode,
            "default_template_id" : template_id,
            "default_use_template" : bool(template_id)
        }
        
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": email_context,
        }
          
    def send_mail_supplier_one(self, cr, uid, ids, context=None):        
        if context is None:
            context = {}
        else:
            context = dict(context)
            
        context["except_supplier_mail_sent"]=True
        return self._send_supplier_mail(cr, uid, ids, context)
    
    
    def assign_selected_partner(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if ids:
            sale_line_obj = self.pool["sale.order.line"]
            for line in self.browse(cr, uid, ids, context=context):
                sale_line = line.sale_line_id
                if sale_line:
                    sale_line_obj.write(cr, uid, [sale_line.id], {"supplier_id" : line.partner_id.id,
                                                                  "supplier_price" : line.price_unit })
                    
                    unselect_ids = self.search(cr, uid, [("sale_line_id","=",sale_line.id),("id","!=",line.id)])
                    self.write(cr, uid, unselect_ids, {"quot_selected":False}, context=context)
                    self.write(cr, uid, [line.id], {"quot_selected":True}, context=context)
            
        return True
  
    
    _inherit = "purchase.order.line"
    _columns = {
       "quot_selected" : fields.boolean("Selected"),
       "quot_sent" : fields.boolean("Selected"),
       "pricelist_price" : fields.function(_get_pricelist_price, type="float", string="Pricelist Price")
    }   
    
    
class mail_compose_message(osv.TransientModel):

    def send_mail(self, cr, uid, ids, context=None):
        if context and context.get("active_model") == "purchase.order" and context.get("context_origin") == "_send_supplier_mail":
            active_ids = context.get("active_ids")
            if active_ids:
                
                # mark sent
                purchase_line_obj = self.pool["purchase.order.line"]
                mark_send_ids = purchase_line_obj.search(cr, uid, [("order_id","in",active_ids)], context=context)
                purchase_line_obj.write(cr, uid, mark_send_ids, {"quot_sent":True}, context=context)
                
                # signal workflow                 
                context = dict(context)
                # prevent trigger again in inherited method of addons/purchase/purchase.py               
                context["default_res_id"]=None
                context["mail_post_autofollow"]=True
                self.pool["purchase.order"].signal_workflow(cr, uid, active_ids, 'send_rfq')

        return super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)

    _inherit = "mail.compose.message" 