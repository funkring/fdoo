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
from openerp import SUPERUSER_ID

class stock_picking(osv.osv):

    def _create_invoice_from_picking(self, cr, uid, picking, vals, context=None):
        if picking and picking.shop_id:
            vals["shop_id"] = picking.shop_id.id
        return super(stock_picking,self)._create_invoice_from_picking(cr, uid, picking, vals, context=context)

    def _relids_sale_order(self, cr, uid, ids, context=None):
        if not ids:
            return []
        
        cr.execute("SELECT p.id FROM sale_order s "
                   " INNER JOIN stock_picking p ON p.group_id = s.procurement_group_id "
                   " WHERE s.id IN %s "
                   " GROUP BY 1 ", (tuple(ids),))
                   
        res = [r[0] for r in cr.fetchall()]
        return res

    def _relids_picking(self, cr, uid, ids, context=None):
        if not ids:
            return []
        cr.execute("SELECT m.picking_id FROM stock_move m WHERE m.id IN %s GROUP BY 1", (tuple(ids),))
        res = [r[0] for r in cr.fetchall()]
        return res

    def _sale_id(self, cr, uid, ids, field_names, arg, context=None):
        sale_obj = self.pool.get("sale.order")
        res = dict.fromkeys(ids)
        
        for oid in ids:
            res[oid] = {"sale_id" : None, 
                        "shop_id" : None}
        
        cr.execute("SELECT p.id, s.id, s.shop_id FROM stock_picking p "
                   " INNER JOIN sale_order s ON s.procurement_group_id = p.group_id "
                   " WHERE p.id IN %s "
                   " GROUP BY 1,2,3 "
                   " ORDER BY p.id, s.date_order DESC, s.id DESC ", (tuple(ids),))
        
        last_picking_id = None
        
        for picking_id, order_id, shop_id in cr.fetchall():
            if not last_picking_id or picking_id != last_picking_id:
                res[picking_id]["sale_id"] = order_id
                res[picking_id]["shop_id"] = shop_id
            last_picking_id = picking_id
            
        return res

    
    
    _inherit = "stock.picking"
    _columns = {
        "sale_id": fields.function(_sale_id, type="many2one", relation="sale.order", string="Sale Order", multi="_sale_id",  store={
                                       "sale.order" : (_relids_sale_order,["procurement_group_id"], 20),
                                       "stock.move": (_relids_picking, ["picking_id"], 20),
                                       "stock.picking": (lambda self, cr, uid, ids, context=None: ids, ["move_lines"], 20)

                                   }),
        "shop_id": fields.function(_sale_id, type="many2one", relation="sale.shop", string="Sale Shop", multi="_sale_id",  store={
                                       "sale.order" : (_relids_sale_order,["procurement_group_id"], 20),
                                       "stock.move": (_relids_picking, ["picking_id"], 20),
                                       "stock.picking": (lambda self, cr, uid, ids, context=None: ids, ["move_lines"], 20)                                       
                                   })
    }
