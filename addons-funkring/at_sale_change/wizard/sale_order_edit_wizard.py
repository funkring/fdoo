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
    modify = fields.Boolean("Modify")
    

class sale_order_edit_wizard(models.TransientModel):
    _name = "sale.order.edit.wizard"
    _description = "Modify Wizard"
    
    def _default_line_ids(self):
        res = []
        active_model = self._context.get("active_model")
        if active_model == "sale.order":
            active_id = self._context.get("active_id")
            if active_id:
                order = self.env["sale.order"].browse(active_id)                
                for line in order.order_line:                    
                    res.append((0,0,{
                        "line_id" : line.id,
                        "name" : line.name,
                        "discount" : line.discount,
                        "modify" : False
                    }))        
        return res
        
    line_ids = fields.One2many("sale.order.edit.wizard.line", "wizard_id", "Lines", default=_default_line_ids)
    
    @api.multi
    def action_modify(self):
        if self.env.user.has_group("base.group_sale_manager"):            
            for line in self.line_ids:
                if line.modify:
                    line.line_id.write({
                        "name" : line.name,
                        "discount" : line.discount
                    })
        return True
