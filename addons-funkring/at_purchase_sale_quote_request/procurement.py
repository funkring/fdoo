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

from openerp.osv import osv
  
class procurement_order(osv.osv):
    
    def create_procurement_purchase_order(self, cr, uid, procurement, po_vals, line_vals, context=None):
        move_dest_id = line_vals.get("move_dest_id",None)
        partner_id = po_vals.get("partner_id",None)
        if move_dest_id and partner_id:
            stock_move_obj = self.pool.get("stock.move")
            sale_line_name = stock_move_obj.read(cr,uid,move_dest_id,["sale_line_id"])["sale_line_id"]          
            if sale_line_name:
                purchase_order_obj = self.pool.get("purchase.order")
                purchase_order_line_obj = self.pool.get("purchase.order.line")                
                ids = purchase_order_line_obj.search(cr,uid,[("origin_sale_order_line_id","=",sale_line_name[0])])                
                for poline in purchase_order_line_obj.browse(cr,uid,ids,context):
                    if poline.partner_id.id == partner_id and not poline.move_dest_id:
                        purchase_order = poline.order_id
                        if purchase_order:
                            purchase_order_obj.write(cr,uid,purchase_order.id,po_vals,context)            
                            purchase_order_line_obj.write(cr,uid,poline.id,line_vals,context)
                            return purchase_order.id
                                
        res = super(procurement_order,self).create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context=context)
        return res
    
    _inherit = "procurement.order"    
