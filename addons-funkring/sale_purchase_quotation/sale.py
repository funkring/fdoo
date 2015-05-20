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


class sale_order(osv.Model):

    _inherit = 'sale.order'

    def action_wait(self, cr, uid, ids, context=None):
        context = context or {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        purchase_order_obj = self.pool.get('purchase.order')
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        obj_data = self.pool.get('ir.model.data')
        for o in self.browse(cr, uid, ids):
            if not o.order_line:
                raise osv.except_osv(_('Error!'), _('You cannot confirm a sales order which has no line.'))
            supplier_ids = []
            line_dict = {}
            for line in o.order_line:
                if line.supplier_id:
                    if line.supplier_id.id not in supplier_ids:
                        supplier_ids.append(line.supplier_id.id)
                    if line_dict.get(line.supplier_id.id, False):
                        line_dict[line.supplier_id.id].append(line.id)
                    else:
                        line_dict[line.supplier_id.id] = [line.id]
            for supplier_id in supplier_ids:
                obj_ref = obj_data.get_object_reference(cr, uid, 'stock', 'picking_type_in')
                picking_type_id = obj_ref and obj_ref[1] or False,
                picktype = False
                if picking_type_id:
                    picktype = self.pool.get("stock.picking.type").browse(cr, uid, picking_type_id, context=context)
                purchase_res = {'partner_id' : supplier_id, 'date_order' : fields.datetime.now(),
                               'state': 'draft', 'name': '/', 'shipped': 0, 'invoice_method': 'order', 'invoiced': 0,
                               'pricelist_id' : self.pool.get('res.partner').browse(cr, uid, supplier_id).property_product_pricelist_purchase.id,
                               'company_id' : self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.order', context=context),
                               'currency_id' : self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id,
                               'picking_type_id' : picking_type_id,
                               'location_id' : picktype and picktype.default_location_dest_id and picktype.default_location_dest_id.id or False,
                               'order_line' : []}
                for line_rec in sale_order_line_obj.browse(cr, uid, line_dict.get(supplier_id, []), context=context):
                    line_dict_line = purchase_order_line_obj.onchange_product_id(cr, uid, [], purchase_res.get('pricelist_id'),
                                                                                 line_rec.product_id.id, line_rec.product_uom_qty,
                                                                                 line_rec.product_uom.id, supplier_id, purchase_res.get('date_order'))
                    line_dict_line = line_dict_line.get('value', {})
                    line_dict_line.update({'product_id' : line_rec.product_id.id, 'product_qty' : line_rec.product_uom_qty, 'price_unit' : line_rec.supplier_price})
                    purchase_res['order_line'].append((0, 0, line_dict_line))
                new_purchase_order_id = purchase_order_obj.create(cr, uid, purchase_res, context=context)
                purchase_order_obj.signal_workflow(cr, uid, [new_purchase_order_id], 'purchase_confirm')
        return super(sale_order, self).action_wait(cr, uid, ids, context=context)

class sale_order_line(osv.Model):

    _inherit = 'sale.order.line'

    def create(self, cr, uid, vals, context=None):
        if vals.has_key('dummy_supplier_id'):
            vals['supplier_id'] = vals.get('dummy_supplier_id', False)
        return super(sale_order_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.has_key('dummy_supplier_id'):
            vals['supplier_id'] = vals.get('dummy_supplier_id', False)
        return super(sale_order_line, self).write(cr, uid, ids, vals, context=context)

    def get_sent_email(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=context):
            sent_all = True
            for supplier in rec.supplier_ids:
                if not supplier.send_mail:
                    sent_all = False
            res[rec.id] = sent_all
        return res

    def get_bo_supplier(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=context):
            if not rec.supplier_ids:
                res[rec.id] = False
            else:
                res[rec.id] = True
        return res

    _columns = {
        'supplier_ids' : fields.one2many('sale.line.supplier', 'line_id', 'Suppliers'),
        'supplier_id' : fields.many2one('res.partner', 'Selected Supplier'),
        'dummy_supplier_id' : fields.many2one('res.partner', 'Selected Supplier'),
        'purchase_ok' : fields.boolean('Can be purchase'),
        'sent_to_all' : fields.function(get_sent_email, type="boolean", string="Sent to All"),
        'no_supplier' : fields.function(get_bo_supplier, type="boolean", string="Sent to All"),
        'supplier_price' : fields.float('Supplier Price')
    }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                          lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        ret_val = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
                                                                 uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
                                                                 lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging,
                                                                 fiscal_position=fiscal_position, flag=flag, context=context)
        Product = self.pool['product.product']
        if product:
            product_data = Product.browse(cr, uid, product, context=context)
            supplier_ids = [i.name.id for i in product_data.seller_ids]
            lines = []
            for supplier in supplier_ids:
                lines.append((0, 0, {'partner_id' : supplier, 'product_id' : product, 'product_uom_qty' : qty}))
            ret_val['value'].update({'no_supplier' : bool(supplier_ids), 'supplier_ids' : lines, 'purchase_ok' : product_data.purchase_ok, 'supplier_id' : False, 'dummy_supplier_id' : False})
        return ret_val

    def product_id_change_with_wh(self, cr, uid, ids, pricelist, product, qty=0,
                                  uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                                  lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, warehouse_id=False, context=None):
        ret_val = super(sale_order_line, self).product_id_change_with_wh(cr, uid, ids, pricelist, product, qty=qty,
                                                                         uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
                                                                         lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging,
                                                                         fiscal_position=fiscal_position, flag=flag, warehouse_id=warehouse_id, context=context)
        Product = self.pool['product.product']
        if product:
            product_data = Product.browse(cr, uid, product, context=context)
            supplier_ids = [i.name.id for i in product_data.seller_ids]
            lines = []
            for supplier in supplier_ids:
                lines.append((0, 0, {'partner_id' : supplier, 'product_id' : product, 'product_uom_qty' : qty}))
            ret_val['value'].update({'no_supplier' : bool(supplier_ids), 'supplier_ids' : lines, 'purchase_ok' : product_data.purchase_ok, 'dummy_supplier_id' : False, 'supplier_id' : False})
        return ret_val

    def send_mail_supplier(self, cr, uid, ids, context=None):
        email_template_obj = self.pool.get('email.template')
        sale_line_supplier_obj = self.pool.get('sale.line.supplier')
        for rec in self.browse(cr, uid, ids, context=context):
            supplier_ids = []
            cr_ids = []
            partner_lang = ''
            for supplier in rec.supplier_ids:
                if not supplier.send_mail:
                    if not partner_lang:
                        partner_lang = supplier.partner_id.lang
                    if supplier.partner_id.lang == partner_lang:
                        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale_purchase_quotation', 'email_to_supplier_with_quotation')[1]
                        email_template_obj.write(cr, uid, [template_id], {'email_to' : supplier.partner_id.email,
                                                                          'lang' : partner_lang,
                                                                          'email_from' : rec.order_id.company_id.email,
                                                                          'reply_to' : rec.order_id.user_id.email})
                        supplier_ids.append(supplier.partner_id.id)
                        cr_ids.append(supplier.id)
            if supplier_ids:
                compose_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale_purchase_quotation', 'email_compose_message_wizard_form_inherit')[1]
                ctx = dict(
                    default_model='sale.order.line',
                    default_res_id=rec.id,
                    default_use_template=bool(template_id),
                    default_template_id=template_id,
                    default_composition_mode='mass_mail',
                    curr_ids=cr_ids,
                    default_partner_ids=supplier_ids,
                    from_all_supplier=True,
                    lang=partner_lang
                )
                return {
                    'name': _('Compose Email'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form, 'form')],
                    'view_id': compose_form,
                    'target': 'new',
                    'context': ctx,
                }
            else:
                raise osv.except_osv(_('Warning!'), _('E-mail was already sent to these suppliers!'))
        return True

class sale_line_supplier(osv.osv):

    _name = 'sale.line.supplier'

    def _get_pricelist_price(self, cr, uid, ids, field_name=None, arg=None, context=None):
        """Get price by analyzing the pricelist of the given supplier."""
        res = {}
        product_pricelist = self.pool.get('product.pricelist')
        res_partner = self.pool.get('res.partner')
        for rec in self.browse(cr, uid, ids, context=context):
            res_partner_obj = res_partner.browse(cr, uid, rec.partner_id.id, context=context)
            pricelist_id = res_partner_obj.property_product_pricelist_purchase and res_partner_obj.property_product_pricelist_purchase.id or False
            if pricelist_id:
                price_dict = product_pricelist.price_get(cr, uid, [pricelist_id], rec.product_id.id, rec.product_uom_qty, context=context)
                pricelist_price = price_dict and price_dict[pricelist_id] or 0.0
            else:
                pricelist_price = rec.product_id.standard_price
            res[rec.id] = pricelist_price
        return res

    _columns = {
        'partner_id' : fields.many2one('res.partner', 'Supplier'),
        'product_id' : fields.many2one('product.product', 'Product'),
        'product_uom_qty' : fields.float('Quantity (UOM)'),
        'price' : fields.float('Cost Price'),
        'pricelist_price' : fields.function(_get_pricelist_price, method=True, type="float", string="Pricelist Price"),
        'send_mail' : fields.boolean('E-mail Sent'),
        'selected_supplier' : fields.boolean('Selected Supplier'),
        'line_id' : fields.many2one('sale.order.line', 'Sale Line')
    }

    def on_change_price(self, cr, uid, ids, price, context=None):
        self.write(cr, uid, ids, {'price' : price}, context=context)
        return {'value' : {}}

    def send_mail_supplier_one(self, cr, uid, ids, context=None):
        email_template_obj = self.pool.get('email.template')
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.send_mail:
                raise osv.except_osv(_('Warning!'), _('E-mail was already sent to this supplier!'))
            else:
                template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale_purchase_quotation', 'email_to_supplier_with_quotation')[1]
                email_template_obj.write(cr, uid, [template_id], {'email_to' : rec.partner_id.email,
                                                                  'lang' : rec.partner_id.lang,
                                                                  'email_from' : rec.line_id.order_id.company_id.email,
                                                                  'reply_to' : rec.line_id.order_id.user_id.email})

                compose_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale_purchase_quotation', 'email_compose_message_wizard_form_inherit')[1]
                ctx = dict(
                    default_model='sale.order.line',
                    default_res_id=rec.line_id.id,
                    default_use_template=bool(template_id),
                    default_template_id=template_id,
                    default_composition_mode='comment',
                    curr_ids=[rec.id],
                    default_partner_ids=[rec.partner_id.id],
                    lang=rec.partner_id.lang
                )

                return {
                    'name': _('Compose Email'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form, 'form')],
                    'view_id': compose_form,
                    'target': 'new',
                    'context': ctx,
                }

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

class mail_compose_message(osv.TransientModel):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get('default_model') == 'sale.order.line' and context.get('curr_ids'):
            if context.get('from_all_supplier', False):
                for rec in self.browse(cr, uid, ids, context=context):
                    for partner in rec.partner_ids:
                        new_id = self.copy(cr, uid, rec.id, default={'partner_ids' : []}, context=context)
                        self.write(cr, uid, [new_id], {'partner_ids' : [(4, partner.id)]}, context=context)
                        super(mail_compose_message, self).send_mail(cr, uid, [new_id], context=context)
            else:
                default_res_id = context.get('default_res_id')
                context['active_ids'] = default_res_id and [default_res_id] or None
                context['active_model'] = context.get('default_model', False) and [context.get('default_model')]
                context['active_id'] = context.get('default_res_id', False)
                super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)
            self.pool.get('sale.line.supplier').write(cr, uid, context['curr_ids'], {'send_mail': True}, context=context)
        else:
            super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)
        return {'type': 'ir.actions.act_window_close', 'tag': 'reload'}

