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
                
    _inherit = "stock.picking"
    _columns = {
        "sender_address_id" : fields.function(_sender_address, string="Sender Address", type="many2one", obj="res.partner", store=False),
        "neutral_delivery" : fields.boolean("Neutral Delivery")
    }    
