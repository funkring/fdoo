# -*- encoding: utf-8 -*-
#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martinr@funkring.net>
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

import time

from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

class sale_order_line(osv.Model):

    def _quotation_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=context):
            sent_all = True
            for supplier in rec.supplier_ids:
                if not supplier.send_mail:
                    sent_all = False
            res[rec.id] = sent_all
        return res
    
    def start_quotation(self, cr, uid, ids, context=None):
        supplier_line_obj = self.pool["sale.line.supplier"]
        for line in self.browse(cr, uid, ids, context=context):
            # remove old supplier lines
            supplier_line_ids = supplier_line_obj.search(cr, uid, [("line_id","=",line.id)])
            supplier_line_obj.unlink(cr, uid, supplier_line_ids, context=context)
            
            # create new
            product = line.product_id
            if product:
                supplier_line_ids = []
                for supplier in product.seller_ids:
                     supplier_line_id = supplier_line_obj.create(cr, uid, {"line_id" : line.id,
                                                        "partner_id" : supplier.name.id,
                                                        "product_id" : product.id })
                     supplier_line_ids.append(supplier_line_id)
                
                
                if supplier_line_ids:
                    self.write(cr, uid, line.id, {"quotation_active" : True})
        return True

    def _product_id_change(self, res, flag, product_id, partner_id, lang, context=None):
        res = super(sale_order_line,self)._product_id_change(res, flag, product_id, partner_id, lang, context)
        res["value"].update({"quotation_active" : False})
        return res
   
    def send_mail_supplier(self, cr, uid, ids, context=None):
        email_template_obj = self.pool.get("email.template")
        sale_line_supplier_obj = self.pool.get("sale.line.supplier")
        
        supplier_line_ids = []
        mail_send = 0
        for line in self.browse(cr, uid, ids, context=context):
            for supplier_line in line.supplier_ids:
                supplier_line_ids.append(supplier_line.id)
                if supplier_line.send_mail:
                    mail_send +=1
            
        if supplier_line_ids: 
           
            if mail_send == len(supplier_line_ids):
                raise osv.except_osv(_('Warning!'), _('E-mail was already sent to all supplier!'))

            return sale_line_supplier_obj._send_supplier_mail(cr, uid, supplier_line_ids, context=context)
           
        return True

    _inherit = 'sale.order.line'
    _columns = {
        "supplier_ids" : fields.one2many("sale.line.supplier", "line_id", "Suppliers"),
        "quotation_active" : fields.boolean("Quotation Active"),
        "quotation_all" : fields.function(_quotation_all, type="boolean", string="All Quotation Sent to Suppliers"),
    }


class sale_line_supplier(osv.osv):
    
    def _get_pricelist_price(self, cr, uid, ids, field_name=None, arg=None, context=None):
        """Get price by analyzing the pricelist of the given supplier."""
        res = {}
        product_pricelist = self.pool.get('product.pricelist')
        res_partner = self.pool.get('res.partner')
        for rec in self.browse(cr, uid, ids, context=context):
            res_partner_obj = res_partner.browse(cr, uid, rec.partner_id.id, context=context)
            pricelist_id = res_partner_obj.property_product_pricelist_purchase and res_partner_obj.property_product_pricelist_purchase.id or False
            if pricelist_id:
                price_dict = product_pricelist.price_get(cr, uid, [pricelist_id], rec.product_id.id, rec.line_id.product_uom_qty, context=context)
                pricelist_price = price_dict and price_dict[pricelist_id] or 0.0
            else:
                pricelist_price = rec.product_id.standard_price
            res[rec.id] = pricelist_price
        return res
    
    def on_change_price(self, cr, uid, ids, price, context=None):
        self.write(cr, uid, ids, {'price' : price}, context=context)
        return {'value' : {}}

    def _send_supplier_mail(self, cr, uid, ids, context=None):                
        model_data_obj = self.pool["ir.model.data"]
        template_id = model_data_obj.get_object_reference(cr, uid, "sale_purchase_quotation", "email_to_supplier_with_quotation")[1]
        compose_form = model_data_obj.get_object_reference(cr, uid, "sale_purchase_quotation", "email_compose_message_wizard_form_inherit")[1]
                
        if ids and template_id and compose_form:
            composition_mode = len(ids) > 1 and "mass_mail" or "comment"
            
            partner_ids = set()
            for line in self.browse(cr, uid, ids, context=context):
                partner_ids.add(line.partner_id.id)
                if line.send_mail and context and context.get("except_supplier_mail_sent"):
                    raise osv.except_osv(_('Warning!'), _('E-mail was already sent to this supplier!'))
                
            email_context = {
                "active_ids" : ids,
                "active_model" : "sale.order.line",
                "default_model" : "sale.order.line",                
                "default_partner_ids" : list(partner_ids),      
                "default_composition_mode" : composition_mode,
                "default_template_id" : template_id,
                "default_use_template" : bool(template_id),
                "mark_quotation_send" : True
            }
            
            return {
                    "name": _("Compose Email"),
                    "type": "ir.actions.act_window",
                    "view_type": "form",
                    "view_mode": "form",
                    "res_model": "mail.compose.message",
                    "views": [(compose_form, "form")],
                    "view_id": compose_form,
                    "target": "new",
                    "context": email_context,
            } 
            
        return True

    def send_mail_supplier_one(self, cr, uid, ids, context=None):
        new_context = context and dict(context) or {}
        new_context["except_supplier_mail_sent"]=True
        return self._send_supplier_mail(cr, uid, ids, new_context)

    def assign_selected_partner(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        for rec in self.browse(cr, uid, ids, context=context):
            sale_order_line_obj.write(cr, uid, [rec.line_id.id], {'supplier_id' : rec.partner_id.id,
                                                                  'supplier_price' : rec.price,
                                                                  'dummy_supplier_id' : rec.partner_id.id})
            self.write(cr, uid, [rec.id], {'selected_supplier' : True}, context=context)
            supplier_ids = [x.id for x in rec.line_id.supplier_ids]
            supplier_ids.remove(rec.id)
            self.write(cr, uid, supplier_ids, {'selected_supplier' : False}, context=context)
        return True


    _name = "sale.line.supplier"
    _inherit = ["mail.thread"]
    _columns = {
        "partner_id" : fields.many2one("res.partner", "Supplier", ondelete="cascade", required=True),
        "product_id" : fields.many2one("product.product", "Product", ondelete="cascade", required=True),
        "price" : fields.float("Cost Price"),
        "pricelist_price" : fields.function(_get_pricelist_price, method=True, type="float", string="Pricelist Price"),
        "send_mail" : fields.boolean("E-mail Sent"),
        "selected_supplier" : fields.boolean("Selected Supplier"),
        "line_id" : fields.many2one("sale.order.line", "Sale Line", ondelete="cascade", required=True)
    }
  

class mail_compose_message(osv.TransientModel):
    
    def send_mail(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get("default_model") == "sale.line.supplier" and context.get("mark_quotation_send"):
            line_supplier_obj = self.pool["sale.line.supplier"]
            for wizard in self.browse(cr, uid, arg, context):
                res_ids = self._res_ids(wizard, context)
                line_supplier_obj.write(cr, uid, res_ids, {"send_mail" : True}, context=context)
        return super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)
   
    _inherit = "mail.compose.message"

