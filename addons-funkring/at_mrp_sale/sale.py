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

class sale_order(osv.Model):
    _inherit = "sale.order"
        
    # auto assign
    def action_ship_create(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        production_obj = self.pool["mrp.production"]
        produce_obj = self.pool["mrp.product.produce"]
        
        res = super(sale_order, self).action_ship_create(cr, uid, ids, context=context)
        for order in self.browse(cr, uid, ids, context=context):
            for picking in order.picking_ids:
                if picking.state == "waiting" and picking.picking_type_code == "outgoing":
                    for move in picking.move_lines:
                        productionEntries = production_obj.search_read(cr, uid, 
                                              [("move_prod_id","=",move.id),("product_id","=",move.product_id.id),
                                               ("bom_id.auto_produce","=",True),
                                               ("state","in",["confirmed","ready"])], ["state"], context=context)
                        if productionEntries:
                            for prodEntry in productionEntries:
                                production_id = prodEntry["id"]
                                production_ids = [production_id]
                                
                                # assign
                                if prodEntry["state"] == "confirmed":                                    
                                    production_obj.action_assign(cr, uid, production_ids, context=context)
                                    prodEntry["state"] = production_obj.read(cr, uid, production_id, ["state"], context=context)["state"]
                                    
                                # produce
                                if prodEntry["state"] == "ready":
                                    prodContext = context and dict(context) or {}
                                    prodContext["active_id"] = production_id
                                    prodContext["active_model"] = "mrp.production"
                                    prodContext["active_ids"] = production_ids
                                    values = produce_obj.default_get(cr, uid, ["product_qty","mode","product_id","track_production"], context=prodContext)
                                    values.update(produce_obj.on_change_qty(cr, uid, [], values.get("product_qty",0.0), [], context=prodContext)["value"])
                                    produce_id = produce_obj.create(cr, uid, values, context=prodContext)                            
                                    produce_obj.do_produce(cr, uid, [produce_id], context=prodContext)
                                    produce_obj.unlink(cr, uid, produce_id, context=prodContext)
        return res