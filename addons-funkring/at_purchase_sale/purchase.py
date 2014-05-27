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

class purchase_order(osv.osv):
    _columns = {             
        "supplier_ships" : fields.boolean("Supplier Ships",states={"confirmed":[("readonly",True)], "approved":[("readonly",True)],"done":[("readonly",True)]})
    }
    _inherit = "purchase.order"


class purchase_order_line(osv.osv):      
           
    def _delivery_address_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for line in self.browse(cr, uid, ids):
            dest_partner = line.dest_address_id
            shop = line.shop_id
            if dest_partner:
                res[line.id] = dest_partner.id
            elif shop:
                warehouse = shop.warehouse_id
                company = shop.company_id
                if warehouse and warehouse.partner_id:
                    res[line.id]=warehouse.partner_id.id
                elif company and company.partner_id:
                    res[line.id]=company.partner_id.id
        return res
        
            
    def print_picking(self,cr,uid,ids,context=None):
        print_context = context and context.copy() or {}
        return {            
            "type": "ir.actions.report.xml",
            "report_name": "stock.picking.list_small",
            "datas": {"ids": ids, "model":"purchase.order.line"},
            "context" : print_context
        }    
    
    def confirm_direct_delivery(self, cr, uid, ids, context=None):
        """ Confirm Delivery if it is a direct delivery. """
        """ If it isn't a direct delivery nothing happens """
        
        picking_wizard_obj = self.pool.get("stock.partial.picking")
        picking_obj = self.pool.get("stock.picking")
        picking_dst_ids = []           
        picking_moves = {}
        
        # group all purchase move lines by picking
        selected_purchase_line = None
        for line in self.browse(cr, uid, ids, context):
            selected_purchase_line = line
            if line.supplier_ships:
                # search move lines in
                for move in line.move_ids:
                    picking = move.picking_id
                    if picking:
                        move_ids = picking_moves.get(picking.id)
                        if not move_ids:
                            move_ids = []
                            picking_moves[picking.id]=move_ids
                        move_ids.append(move.id)
                # search picking out
                picking_dest = line.dest_picking_id
                if picking_dest:
                    picking_dst_ids.append(picking_dest.id)
                    
        #confirm picking in and out
        if picking_moves:        
            #confirm all picking in
            for picking_id, move_ids in picking_moves.items():
                picking_context = context and context.copy() or {}
                picking_context["move_line_ids"]=move_ids
                picking_context["active_model"]="stock.picking"
                picking_context["active_ids"]=[picking_id]
                picking_context["active_id"]=picking_id
                #
                wizard_id = picking_wizard_obj.create(cr,uid,{},context=picking_context)
                #use admin rights
                picking_wizard_obj.do_partial(cr, 1, [wizard_id],context=picking_context)
                picking_wizard_obj.unlink(cr,uid,[wizard_id])
            
            #confirm all picking out
            if picking_dst_ids:
                picking_dst_ids = picking_obj.search(cr,uid,[("id","in",picking_dst_ids)])
                for picking_id in picking_dst_ids:
                    picking_context = context and context.copy() or {}
                    picking_context["only_assigned"]=True
                    picking_context["active_model"]="stock.picking"
                    picking_context["active_ids"]=[picking_id]
                    picking_context["active_id"]=picking_id
                    #
                    wizard_id = picking_wizard_obj.create(cr,uid,{},context=picking_context)
                    #use admin rights
                    picking_wizard_obj.do_partial(cr, 1, [wizard_id], context=picking_context)
                    picking_wizard_obj.unlink(cr,uid,[wizard_id])
                
        if selected_purchase_line:
            return self.print_picking(cr, uid, [selected_purchase_line.id], context)                     
        return True   
    
    def _client_order_ref(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT pl.id, s.client_order_ref "
                   " FROM purchase_order_line pl "
                   " INNER JOIN stock_move m ON m.id = pl.move_dest_id "
                   " INNER JOIN sale_order_line sl ON sl.id = m.sale_line_id "
                   " INNER JOIN sale_order s ON s.id = sl.order_id "
                   " WHERE pl.id IN %s "
                   , (tuple(ids),) )
        
        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res
    
    _inherit = "purchase.order.line"
    _columns = {
        "sale_order_line_id" : fields.related("move_dest_id","sale_line_id",type="many2one",relation="sale.order.line", string="Sale Order Line",readonly=True,store=True),
        "sale_order_id" : fields.related("sale_order_line_id","order_id",type="many2one",relation="sale.order", string="Sale Order",readonly=True,store=True,select=True ),
        "dest_address_id" : fields.related("order_id", "dest_address_id", type="many2one", relation="res.partner", string="Destination Address",readonly=True, store=True, select=True),
        "delivery_address_id" : fields.function(_delivery_address_id, type="many2one", obj="res.partner", string="Delivery Address", readonly=True, method=True),
        "supplier_ships" : fields.related("order_id", "supplier_ships", type="boolean",string="Supplier Ships",readonly=True,select=True,store=True),
        "shop_id" : fields.related("sale_order_id","shop_id",type="many2one",relation="sale.shop",string="Shop",readonly=True,store=True,select=True),        
        "client_order_ref" : fields.function(_client_order_ref,type="char",size=64, string="Customer Reference",readonly=True,store=True,select=True)
    }                        
