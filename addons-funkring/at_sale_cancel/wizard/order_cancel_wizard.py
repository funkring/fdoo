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

class sale_order_cancel_wizard(models.TransientModel):
    _name = "sale.order.cancel.wizard"
    _description = "Order Cancel Wizard"
    
    link_ids = fields.One2many("sale.order.cancel.wizard.link", "wizard_id", "Link")
    
    
class sale_order_cancel_wizard_line(models.TransientModel):
    _name = "sale.order.cancel.wizard.link"
    _description = "Order Cancel Wizard Line"
    
    wizard_id = fields.Many2one("sale.order.cancel.wizard", "Wizard")
    name = fields.Char("Name")
    ref = fields.Char("Reference")
    type = fields.Selection([("account.invoice","Invoice"),
                             ("purchase.order","Purchase Order"),
                             ("stock.picking","Picking List")], string="Type")