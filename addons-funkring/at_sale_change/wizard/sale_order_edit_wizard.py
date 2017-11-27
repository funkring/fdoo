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

from openerp import models, fields, api, _
from openerp.exceptions import Warning

class sale_order_edit_wizard_line(models.TransientModel):
    _name = "sale.order.edit.wizard.line"
    _description = "Line"
        
    wizard_id = fields.Many2one("sale.order.edit.wizard", "Wizard", required=True)
    line_id = fields.Many2one("sale.order.line","Line", required=True, readonly=True)    
    name = fields.Text("Name", required=True)
    discount = fields.Float("Discount")
    price_unit = fields.Float("Price")
    qty = fields.Float("Quantity")
    price_subtotal = fields.Float("Total", readonly=True)   
    route_id = fields.Many2one("stock.location.route", "Route", domain=[("sale_selectable", "=", True)])
    modify = fields.Boolean("Modify")
    
    @api.multi
    def onchange_line(self, line_id, name, discount, price_unit, qty, route_id, modify):
        value = {}
        res = {"value": value}
        
        line = self.env["sale.order.line"].browse(line_id)
        
        price = price_unit * (1-(discount or 0.0) / 100.0)
        taxes = line.tax_id.compute_all(price, qty, line.product_id, line.order_id.partner_id)
        cur = line.order_id.pricelist_id.currency_id
        value["price_subtotal"] = cur.round(taxes["total"])
        value["modify"] = True
        return res
    

class sale_order_edit_wizard(models.TransientModel):
    _name = "sale.order.edit.wizard"
    _description = "Modify Wizard"
    
    @api.model
    def default_get(self, fields_list):
        res = super(sale_order_edit_wizard, self).default_get(fields_list)
        
        active_model = self._context.get("active_model")
        if active_model == "sale.order":
            active_id = self._context.get("active_id")
            if active_id:
                order = self.env["sale.order"].browse(active_id)
                if "order_id" in fields_list:
                    res["order_id"] = order.id
                if "date_order"  in fields_list:
                    res["date_order"] = order.date_order
                if "partner_id" in fields_list:
                    res["partner_id"] = order.partner_id.id
                if "partner_invoice_id" in fields_list:
                    res["partner_invoice_id"] = order.partner_invoice_id.id
                if "partner_shipping_id" in fields_list:
                    res["partner_shipping_id"] = order.partner_shipping_id.id
                if "line_ids" in fields_list:
                    default_line_ids = []
                    res["line_ids"] = default_line_ids
                    for line in order.order_line:                    
                        default_line_ids.append((0,0,{
                            "line_id" : line.id,
                            "name" : line.name,
                            "discount" : line.discount,
                            "price_unit" : line.price_unit,
                            "price_subtotal" : line.price_subtotal,
                            "qty" : line.product_uom_qty,
                            "route_id": line.route_id.id,
                            "modify" : False
                        }))     
                
        
        return res
        
        
    
    order_id = fields.Many2one("sale.order", "Order", required=True, readonly=True)
    date_order = fields.Datetime("Date", required=True)
    partner_id = fields.Many2one("res.partner", "Partner", required=True)
    partner_invoice_id = fields.Many2one("res.partner","Invoice Address", required=True)
    partner_shipping_id = fields.Many2one("res.partner","Delivery Address", required=True)
    line_ids = fields.One2many("sale.order.edit.wizard.line", "wizard_id", "Lines")
    modify = fields.Boolean("Modify")
    
    @api.multi
    def action_modify(self):
      procurement_obj = self.env["procurement.order"]
      for modify_wizard in self:
        if self.env.user.has_group("base.group_sale_manager"):
            # line modify
            for line in modify_wizard.line_ids:
                if modify_wizard.modify:
                  
                    order = self.order_id
                    sale_line = line.line_id
                  
                    new_route = line.route_id
                    cur_route = sale_line.route_id
                    
                    values = {
                        "name" : line.name,
                        "discount" : line.discount,
                        "price_unit" : line.price_unit,
                        "product_uom_qty" : line.qty                    
                    }
                    
                    # get line values
                    line_values = sale_line.product_id_change_with_wh_price(order.pricelist_id.id, sale_line.product_id.id, qty=line.qty,
                                                    uom=sale_line.product_uom.id, name=line.name, partner_id=order.partner_id.id,
                                                    update_tax=False, date_order=order.date_order, flag=True, 
                                                    warehouse_id=order.warehouse_id.id, 
                                                    route_id=line.route_id.id, 
                                                    price_unit=line.price_unit, price_nocalc=True)["value"]
                                                    
                    values["product_uos_qty"] = line_values.get("product_uos_qty")
                    values["product_uos"] = line_values.get("product_uos") 
                    
                    # check modify route
                    # only if procurement is needed
                    if new_route.id != cur_route.id and sale_line.need_procurement():
                      procurements = procurement_obj.search([("sale_line_id","=",sale_line.id)])
                      procurements.cancel()
                      
                      # update values
                      values["route_id"] = new_route.id
                      sale_line.write(values)
                      
                      # get procurement vals
                      procurement_vals = order._prepare_order_line_procurement(order, sale_line, group_id=order.procurement_group_id.id)
                      # create new procurement
                      procurement = procurement_obj.with_context({
                        "procurement_autorun_defer": True
                      }).create(procurement_vals)
                       
                      # run and check procurement 
                      procurement.run()
                      procurement.check()              
                      
                      # cleanup lines
                      for picking in order.picking_ids:
                        if not picking.state in ("done","cancel"):
                          moves = picking.move_lines
                          deleted_moves = 0
                          for move in moves:
                            # delete line if canceled
                            if move.state == "cancel":
                              move.unlink()
                              deleted_moves+=1
                              
                          # delete picking if empty
                          if deleted_moves == len(moves):
                            picking.unlink()
                    
                    else:
                      
                      # update values without procurement modify
                      sale_line.write(values)
                    
            # order modify
            if self.modify:
                self.order_id.date_order = self.date_order
                self.order_id.partner_id = self.partner_id
                self.order_id.partner_invoice_id = self.partner_invoice_id
                self.order_id.partner_shipping_id = self.partner_shipping_id
                
      return True
