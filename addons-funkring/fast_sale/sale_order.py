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

class sale_order(models.Model):
    
    _inherit = "sale.order"

    @api.multi
    def action_deliver_invoice(self):
        for order in self:
            # if in draft confirm
            if order.state == "draft":
                order.order_policy = "manual"
                order.action_button_confirm()
            
            # do delivery
            for picking in order.picking_ids:
                picking.force_assign()
                picking.do_transfer()
        
        return self.manual_invoice()
