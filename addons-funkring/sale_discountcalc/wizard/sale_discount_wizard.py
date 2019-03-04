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
import openerp.addons.decimal_precision as dp
from openerp.addons.at_base import util 
from openerp.exceptions import Warning

class sale_discount_wizard(models.TransientModel):
  _name = "sale.discount.wizard"
  _description = "Sale Discount Wizard"
    
  @api.model
  def _default_total(self):
    order_id = util.active_id(self._context, "sale.order")
    total = 0.0
    if order_id:
      order = self.env["sale.order"].browse(order_id)
      for line in order.order_line:
        total += (line.product_uom_qty * line.price_unit)
    return total
  
    
  type = fields.Selection([("total","Total Price"),
                           ("percent", "Discount %"),
                           ("discount", "Discount"),
                           ("reset", "Reset")],
                           string="Discount Type", default="total", required=True)
  
  amount = fields.Float("Amount", digits_compute=dp.get_precision("Account"), required=True)
  
  total = fields.Float("Total", digits_compute=dp.get_precision("Account"), default=_default_total)
                  
  order_id = fields.Many2one("sale.order", "Order", required=True, default=lambda self: util.active_id(self._context, "sale.order"))
  
  is_action = fields.Boolean("Action")
                        
  @api.multi                 
  def action_apply(self):
    for wizard in self:
      if wizard.type == "reset":
        for line in wizard.order_id.order_line:
          if not line.discount_price:
            line.discount = 0.0            
      else:
        total = 0.0
        discount_price = 0.0
        apply_to_lines = []
        for line in wizard.order_id.order_line:
          if not line.discount_price:
            apply_to_lines.append(line)
            taxes = line.tax_id.compute_all(line.price_unit, line.product_uom_qty,
                                         line.product_id.id, line.order_id.partner_id.id)
            total += taxes["total_included"]
          else:
            qty = line.product_uom_qty or 1
            taxes = line.tax_id.compute_all(line.discount_price / qty, qty,
                                         line.product_id.id, line.order_id.partner_id.id)
            discount_price += taxes["total_included"]
        
        if not total or not apply_to_lines:
          raise Warning(_("Unable to apply overall discount for amount %s and lines %s") % (total,len(apply_to_lines)))
              
        if wizard.type == "total":
          discount = 100.0-(100.0/total*(wizard.amount-discount_price))      
        elif wizard.type == "discount":
          discount = 100.0-(100.0/total*(total-wizard.amount-discount_price))
        else:
          discount = wizard.amount
        
        for line in apply_to_lines:
          line.discount = discount
          line.discount_action = wizard.is_action
        
    return True
         