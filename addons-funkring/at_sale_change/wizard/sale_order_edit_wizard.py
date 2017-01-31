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
    modify = fields.Boolean("Modify")
    
    @api.multi
    def onchange_line(self, line_id, name, discount, price_unit, qty, modify):
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
                            "modify" : False
                        }))     
                
        
        return res
        
        
    
    order_id = fields.Many2one("sale.order", "Order", required=True, readonly=True)
    date_order = fields.Datetime("Date", required=True)    
    line_ids = fields.One2many("sale.order.edit.wizard.line", "wizard_id", "Lines")
    modify = fields.Boolean("Modify")
    
    @api.multi
    def action_modify(self):
        if self.env.user.has_group("base.group_sale_manager"):
            # line modify
            for line in self.line_ids:
                if line.modify:
                    line.line_id.write({
                        "name" : line.name,
                        "discount" : line.discount,
                        "price_unit" : line.price_unit,
                        "product_uom_qty" : line.qty
                    })
                    
            # order modify
            if self.modify:
                self.order_id.date_order = self.date_order
                
        return True
