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
from openerp import SUPERUSER_ID, api
from openerp.tools.float_utils import float_compare

import re

MATCH_BARCODE_STOCK_MOVE = re.compile("^SM([0-9]+)$")


class stock_pack_operation(osv.osv):
    
    def _pack_description(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            description = []
            for link in obj.linked_move_operation_ids:
                description.append(link.move_id.name)
            res[obj.id] = "\n".join(description)
        return res
    
    def _pack_calc(self, cr, uid, ids, field_name, arg, context=None):
        
        res = dict.fromkeys(ids,0)
        for obj in self.browse(cr, uid, ids, context):
            # count
            package_count=0
            ops=set()

            # search back
            for link in obj.linked_move_operation_ids:
                for move_org in link.move_id.move_orig_ids:
                    for link_org in move_org.linked_move_operation_ids:
                        # add package count from operation
                        operation = link_org.operation_id
                        if operation.id != obj.id and not operation.id in ops:
                            ops.add(operation.id)
                            package_count+=operation.package_count
            
            # set count    
            res[obj.id] = package_count
            
        return res
            
    _inherit = "stock.pack.operation"
    _columns = {
        "name" : fields.function(_pack_description, type="char", store=False, string="Description"),
        "package_count" : fields.integer("Packages"),
        "package_calc" : fields.function(_pack_calc, type="integer", store=False, string="Expected Packages")
    }
    _defaults = {
        "package_count" : 1
    }


class stock_move(osv.osv):
    
    def _prepare_procurement_from_move(self, cr, uid, move, context=None):
        """ 
         since new version of odoo routing a procurement could initiate 
         another procurement, sale_line_id should also be copied
        """
        res = super(stock_move,self)._prepare_procurement_from_move(cr, uid, move, context=context)
        source_procurement = move.procurement_id
        
        if source_procurement:                        
            sale_line = source_procurement.sale_line_id
            if sale_line:
                if not "sale_line_id" in res:
                    res["sale_line_id"] = sale_line.id
                    
        return res
    
    def action_confirm(self, cr, uid, ids, context=None):
        """
            Pass neutral delivery flag to the picking from the sales order
            (Should also work in case of Phantom BoMs when on explosion the original move is deleted)
        """
        procs_to_check = []
        for move in self.browse(cr, uid, ids, context=context):
            if move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id.order_id.neutral_delivery:
                procs_to_check += [move.procurement_id]
        res = super(stock_move, self).action_confirm(cr, uid, ids, context=context)
        pick_obj = self.pool.get("stock.picking")
        for proc in procs_to_check:
            pickings = list(set([x.picking_id.id for x in proc.move_ids if x.picking_id and not x.picking_id.neutral_delivery]))
            if pickings:
                pick_obj.write(cr, uid, pickings, {'neutral_delivery': proc.sale_line_id.order_id.neutral_delivery}, context=context)
        return res

        
    _inherit = "stock.move"


class stock_picking(osv.osv):
        
    def _sender_address(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for picking in self.browse(cr, uid, ids, context):
            sale_order = picking.sale_id
            
            # check neutral delivery
            if sale_order and picking.neutral_delivery:
                res[picking.id] = sale_order.partner_id
                
            else:
                # default partner from company            
                partner = None
                
                # check address from shop 
                shop = picking.shop_id
                if shop and shop.sender_address_id:
                    partner = shop.sender_address_id
                        
                # check address from location
                if not partner and picking.location_id:
                    partner = picking.location_id.partner_id
                    
                # use company address
                if not partner:
                    partner = picking.company_id.partner_id
                    
                res[picking.id]=partner.id
                    
        return res
    
    def _simple_type(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for picking in self.browse(cr, uid, ids, context):
            type_code = picking.picking_type_code
            res[picking.id] = type_code
            if type_code == "incoming":
                dest_id = picking.picking_type_id.default_location_dest_id
                if dest_id.usage == "customer":
                    res[picking.id] = "dropshipment"        
        return res
    
    def add_package(self, cr, uid, picking_id, op_id, inc, context=None):
        stock_operation_obj = self.pool["stock.pack.operation"]
        op = stock_operation_obj.browse(cr, uid, op_id, context=context)
        if inc > 0:
            stock_operation_obj.write(cr, uid, op.id, {"package_count" : op.package_count + inc}, context=context)
        elif inc < 0:
            next_package_count = op.package_count+inc
            if next_package_count <= 0:
                stock_operation_obj.write(cr, uid, op.id, {"package_count" : 0}, context=context)
            else:
                stock_operation_obj.write(cr, uid, op.id, {"package_count" : next_package_count}, context=context)
        return True
    
    def process_barcode_from_ui(self, cr, uid, picking_id, barcode_str, visible_op_ids, context=None):
        m = MATCH_BARCODE_STOCK_MOVE.match(barcode_str)
        if m:
            res = {"filter_loc": False, "operation_id": False}
            move_id = int(m.group(1))
            
            # check package based scan
            stock_operation_obj = self.pool["stock.pack.operation"]
            op_id = stock_operation_obj.search_id(cr, uid, [("picking_id","=",picking_id),("linked_move_operation_ids.move_id","=",move_id)], context=context)
            if op_id and not visible_op_ids or op_id in visible_op_ids:
                op = stock_operation_obj.browse(cr, uid, op_id, context=context)
                if op.package_calc:
                    # close op
                    if  op.package_count+1 == op.package_calc:
                        # finish op
                        stock_operation_obj.write(cr, uid, op_id, {"qty_done" : op.product_qty}, context=context)
                    
                    # increment
                    stock_operation_obj.write(cr, uid, op_id, {"package_count" : op.package_count+1 }, context=context)
                    res["operation_id"] = op_id
                    return res
                else:
                    # finish
                    stock_operation_obj.write(cr, uid, op_id, {"qty_done" : op.product_qty}, context=context)
                    res["operation_id"] = op_id
                    return res
            
            # default operation
            if op_id:
                op_id = stock_operation_obj._search_and_increment(cr, uid, picking_id, [("id","=",op_id)], filter_visible=True, visible_op_ids=visible_op_ids, increment=True, context=context)
                res["operation_id"] = op_id
            return res            
        else:
            return super(stock_picking, self).process_barcode_from_ui(cr, uid, picking_id, barcode_str, visible_op_ids, context=context)
    
    def print_delivery(self, cr, uid, ids, context=None):
        '''This function prints the picking list'''
        ctx = dict(context or {}, active_ids=ids)
        return self.pool.get("report").get_action(cr, uid, ids, 'stock.delivery.report', context=ctx)
    
    def print_shipping(self, cr, uid, ids, context=None):
        # default disable max_package count
        ctx = context and dict(context) or {}
        if not "max_package_count" in ctx:
            ctx["max_package_count"] = None
        
        # prepare report
        move_ids = set()
        picking_ids = set()
        for picking in self.browse(cr, uid, ids, context=context):        
            for line in picking.move_lines:
                # get destination picking
                if line.move_dest_id:
                    move_dest = line.move_dest_id
                    picking_dest = move_dest.picking_id
                    if picking_dest:
                        move_ids.add(move_dest.id)
                        picking_ids.add(picking_dest.id)
                # add
                else:
                    picking_ids.add(picking.id)
                    move_ids.add(line.id)
                    
        ids = list(picking_ids)
        ctx["active_ids"] = ids
        ctx["move_ids"] = list(move_ids)
        return self.pool.get("report").get_action(cr, uid, ids, "stock.delivery.label", context=ctx)
    
    def print_shipping_one(self, cr, uid, ids, context=None):
        ctx = context and dict(context) or {}
        ctx["max_package_count"] = 1
        return self.print_shipping(cr, uid, ids, context=ctx)

    @api.cr_uid_ids_context
    def do_prepare_partial(self, cr, uid, picking_ids, context=None):
        context = context or {}
        pack_operation_obj = self.pool.get('stock.pack.operation')
        #used to avoid recomputing the remaining quantities at each new pack operation created
        ctx = context.copy()
        ctx['no_recompute'] = True

        #get list of existing operations and delete them
        existing_package_ids = pack_operation_obj.search(cr, uid, [('picking_id', 'in', picking_ids)], context=context)
        if existing_package_ids:
            pack_operation_obj.unlink(cr, uid, existing_package_ids, context)
        for picking in self.browse(cr, uid, picking_ids, context=context):
            forced_qties = {}  # Quantity remaining after calculating reserved quants
            picking_quants = []
            #Calculate packages, reserved quants, qtys of this picking's moves
            for move in picking.move_lines:
                if move.state not in ('assigned', 'confirmed', 'waiting'):
                    continue
                
                # prepare
                move_quants = move.reserved_quant_ids                
                forced_qty = (move.state == 'assigned') and move.product_qty - sum([x.qty for x in move_quants]) or 0
                
                # single pack operation if type consumable        
                if move.product_id.type == "consu":
                    for vals in self._prepare_pack_ops(cr, uid, picking, move_quants, { move.product_id : forced_qty }, context=context):
                        pack_operation_obj.create(cr, uid, vals, context=ctx)
                    continue
                
                picking_quants += move_quants
                
                #if we used force_assign() on the move, or if the move is incoming, forced_qty > 0
                if float_compare(forced_qty, 0, precision_rounding=move.product_id.uom_id.rounding) > 0:
                    if forced_qties.get(move.product_id):
                        forced_qties[move.product_id] += forced_qty
                    else:
                        forced_qties[move.product_id] = forced_qty
                
            for vals in self._prepare_pack_ops(cr, uid, picking, picking_quants, forced_qties, context=context):
                pack_operation_obj.create(cr, uid, vals, context=ctx)
                
        #recompute the remaining quantities all at once
        self.do_recompute_remaining_quantities(cr, uid, picking_ids, context=context)
        self.write(cr, uid, picking_ids, {'recompute_pack_op': False}, context=context)
    
  
    _inherit = "stock.picking"
    _columns = {
        "sender_address_id" : fields.function(_sender_address, string="Sender Address", type="many2one", obj="res.partner", store=False),
        "neutral_delivery" : fields.boolean("Neutral Delivery"),
        "simple_type" : fields.function(_simple_type, string="Type", type="char")
    }    
