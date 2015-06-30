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

import openerp
from openerp import models, fields, api, _
from openerp.addons.at_base.format import LangFormat

class fclipboard_item(models.Model):
    
    @api.one
    def _compute_value(self):
        if self.type == "c":
            return self.valc
        elif self.type == "t":
            return self.valt
        elif self.type == "i":
            if type(self.vali) in (int,long):
                return str(self.vali)
            return None
        elif self.type == "f":
            f = LangFormat()
            f.formatLang(self.valf)
        elif self.type == "d":
            f = LangFormat()
            f.formatLang(self.vald,date=True)
        return None
    
    @api.one   
    @api.depends("parent_id")
    def _compute_root_id(self):
        if self.parent_id:
            self.root_id = self.parent_id.root_id.id
        else:
            self.root_id = self.id
        
    # fields
    name = fields.Char("Name", required=True, select=True)
    code = fields.Char("Code", select=True)
    type = fields.Selection([("n","Directory"),
                             ("c","Char"),
                             ("t","Text"),
                             ("i","Integer"),
                             ("f","Float"),
                             ("b","Boolean"),    
                             ("d","Date"),                         
                            ],"Type", select=True, required=True)
    
    pos = fields.Selection([(1,"Master"),
                            (2,"Detail")],
                           "Position", select=True, required=True)
    
    ref = fields.Reference([("res.partner","Partner"),
                            ("product.product","Product"),
                            ("sale.order","Sales Order")], string="Reference", select=True)
    
    owner_id = fields.Many2one("res.users", "Owner", ondelete="set null")
    is_template = fields.Boolean("Template")
    
    root_id = fields.Many2one("fclipboard.item","Root", select=True, compute="_compute_root_id", readonly=True)
    parent_id = fields.Many2one("fclipboard.item","Parent", select=True, ondelete="cascade")
    child_ids = fields.One2many("fclipboard.item","parent_id", "Childs")
    
    sequence = fields.Integer("Sequence")
    
    valc = fields.Char("Value", help="String Value")
    valt = fields.Text("Value", help="Text Value")
    valf = fields.Float("Value", help="Float Value")
    vali = fields.Integer("Value", help="Integer Value")
    valb = fields.Boolean("Value", help="Boolean Value")
    vald = fields.Date("Value", help="Date Value")    
    value = fields.Text("Value",readonly=True, _compute="_compute_value")
  
    # main definition
    _name = "fclipboard.item"
    _description = "Item"  
    _order = "pos, sequence"
    _defaults = {
        "sequence" : 20,
        "pos" : 1
    }
    