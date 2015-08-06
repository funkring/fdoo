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

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _

class procurement_order(osv.Model):

    def _get_product_supplier(self, cr, uid, procurement, context=None):
        ''' returns the main supplier of the procurement's product given as argument'''
        res = procurement.sale_line_id.supplier_id
        if not res:
            return super(procurement_order,self)._get_product_supplier(cr, uid, procurement, context=context)
        
    def make_po(self, cr, uid, ids, context=None):
        """ Resolve the purchase from procurement, which may result in a new PO creation, a new PO line creation or a quantity change on existing PO line.
        Note that some operations (as the PO creation) are made as SUPERUSER because the current user may not have rights to do it (mto product launched by a sale for example)

        --> This version of make_po is without Grouping

        @return: dictionary giving for each procurement its related resolving PO line.
        """
        res = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        po_obj = self.pool.get('purchase.order')
        po_line_obj = self.pool.get('purchase.order.line')
        seq_obj = self.pool.get('ir.sequence')
        pass_ids = []
        linked_po_ids = []
        sum_po_line_ids = []
        for procurement in self.browse(cr, uid, ids, context=context):
            partner = self._get_product_supplier(cr, uid, procurement, context=context)
            if not partner:
                self.message_post(cr, uid, [procurement.id], _('There is no supplier associated to product %s') % (procurement.product_id.name))
                res[procurement.id] = False
            else:
                sale_line = procurement.sale_line_id
                schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)
                line_vals = self._get_po_line_values_from_proc(cr, uid, procurement, partner, company, schedule_date, context=context)
                #look for any other draft PO for the same supplier, to attach the new line on instead of creating a new draft one
                name = seq_obj.get(cr, uid, 'purchase.order') or _('PO: %s') % procurement.name
                po_vals = {
                    'name': name,
                    'origin': procurement.origin,
                    'partner_id': partner.id,
                    'location_id': procurement.location_id.id,
                    'picking_type_id': procurement.rule_id.picking_type_id.id,
                    'pricelist_id': partner.property_product_pricelist_purchase.id,
                    'currency_id': partner.property_product_pricelist_purchase and partner.property_product_pricelist_purchase.currency_id.id or procurement.company_id.currency_id.id,
                    'company_id': procurement.company_id.id,
                    'fiscal_position': po_obj.onchange_partner_id(cr, uid, None, partner.id, context=context)['value']['fiscal_position'],
                    'payment_term_id': partner.property_supplier_payment_term.id or False,
                    'dest_address_id': procurement.partner_dest_id.id,
                    'notes': sale_line.procurement_note
                }
                po_id = self.create_procurement_purchase_order(cr, SUPERUSER_ID, procurement, po_vals, line_vals, context=context)
                po_line_id = po_obj.browse(cr, uid, po_id, context=context).order_line[0].id
                pass_ids.append(procurement.id)
                res[procurement.id] = po_line_id
                self.write(cr, uid, [procurement.id], {'purchase_line_id': po_line_id}, context=context)
        if pass_ids:
            self.message_post(cr, uid, pass_ids, body=_("Draft Purchase Order created"), context=context)
        if linked_po_ids:
            self.message_post(cr, uid, linked_po_ids, body=_("Purchase line created and linked to an existing Purchase Order"), context=context)
        if sum_po_line_ids:
            self.message_post(cr, uid, sum_po_line_ids, body=_("Quantity added in existing Purchase Order Line"), context=context)
        return res


    def _get_po_line_values_from_proc(self, cr, uid, procurement, partner, company, schedule_date, context=None):
        """ add requested price from supplier to purchase order """        
        res = super(procurement_order,self)._get_po_line_values_from_proc(cr, uid, procurement, partner, company, schedule_date, context=context)
        sale_line = procurement.sale_line_id
        if sale_line:
            supplier = sale_line.supplier_id
            supplier_line_obj = self.pool["sale.line.supplier"]
            if supplier:
                supplier_line_id = supplier_line_obj.search_id(cr, uid, [("line_id","=",sale_line.id),("partner_id","=",supplier.id)], context=context)
                supplier_line = supplier_line_obj.browse(cr, uid, supplier_line_id, context=context)
                if supplier_line.price:
                    res["price_unit"] = supplier_line.price
        return res

    def create_procurement_purchase_order(self, cr, uid, procurement, po_vals, line_vals, context=None):
        """ use existing purchase order or create new """
        
        sale_order_line =  procurement.sale_line_id

        # check sale line
        if sale_order_line:
            sale_line_supplier_obj = self.pool["sale.line.supplier"]
            supplier_line_id = sale_line_supplier_obj.search_id(cr, uid, [("line_id","=",sale_order_line.id), ("selected_supplier", "=", True)], context=context)
            # check purchase order for line already exist
            if supplier_line_id:
                line_supplier = sale_line_supplier_obj.browse(cr, uid, supplier_line_id, context=context)
                purchase_line = line_supplier.purchase_line_id
                # check if supplier for order line was defined
                if purchase_line:
                    # get purchase order id
                    purchase_id = purchase_line.order_id.id
                    # update purchase order line
                    po_vals.update({"order_line": [(1,purchase_line.id,line_vals)]})
                    self.pool["purchase.order"].write(cr, uid, purchase_id, po_vals, context=context)
                    # return foun id
                    return purchase_id
            else:
                line_vals.update({"name": sale_order_line.name})
                po_vals.update({"order_line": [(0,0,line_vals)],
                                "sale_order_id": sale_order_line.order_id.id})
                return self.pool.get("purchase.order").create(cr, uid, po_vals, context=context)

        # or create new
        return super(procurement_order,self).create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context)

    _inherit = "procurement.order"
