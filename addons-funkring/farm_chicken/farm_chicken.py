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

class chicken_logbook(models.Model):
    
    @api.multi
    def action_start(self):
        return self.write({"state":"active"})
    
    @api.multi
    def action_draft(self):
        return self.write({"state":"draft"})
    
    @api.multi
    def action_done(self):
        return self.write({"state":"done"})
    
    _name = "farm.chicken.logbook"
    _description = "Logbook"
    _inherit = ["mail.thread"]
    _order = "date_start desc"
    
    name = fields.Char("Name", required=True)
    date_start = fields.Date("Start", required=True, index=True, readonly=True, states={'draft': [('readonly', False)]})
    date_end = fields.Date("End", index=True, readonly=True)
    house_id = fields.Many2one("farm.house", string="House", index=True, required=True, readonly=True, states={'draft': [('readonly', False)]})
    chicken_count = fields.Integer("Chicken Count")
    chicken_age = fields.Integer("Chicken Age", help="Chicken age in days")
    state = fields.Selection([("draft","Draft"),
                              ("active","Active"),
                               ("done","Done")],string="State", index=True, default="draft")
        
        
class chicken_log(models.Model):
    
    @api.multi
    def action_draft(self):
        return self.write({"state":"draft"})
    
    @api.multi
    def action_validate(self):
        return self.write({"state":"valid"})
    
    @api.multi
    def action_invalid(self):
        return self.write({"state":"invalid"})
    
    _name = "farm.chicken.log"
    _description = "Log"
    _inherit = ["mail.thread"]
    _order = "day desc, logbook_id"
    
    logbook_id = fields.Many2one("farm.chicken.logbook","Logbook",required=True, index=True)
    day = fields.Date("Day", required=True, readonly=True, index=True, states={'draft': [('readonly', False)]})
    loss = fields.Integer("Loss", readonly=True, states={'draft': [('readonly', False)]})
    weight = fields.Float("Weight", readonly=True, states={'draft': [('readonly', False)]})
    feed = fields.Float("Feet", readonly=True, states={'draft': [('readonly', False)]})
    water = fields.Float("Water", readonly=True, states={'draft': [('readonly', False)]})
    co2 = fields.Float("Co2", readonly=True, states={'draft': [('readonly', False)]})
    temp = fields.Float("Temperature", readonly=True, states={'draft': [('readonly', False)]})
    humidity = fields.Float("Humidity", readonly=True, states={'draft': [('readonly', False)]})
    eggs_total = fields.Integer("Eggs Total", readonly=True, states={'draft': [('readonly', False)]})
    eggs_nest = fields.Integer("Nest Eggs", readonly=True, states={'draft': [('readonly', False)]})
    eggs_top = fields.Integer("Eggs moved above", readonly=True, states={'draft': [('readonly', False)]})
    eggs_buttom = fields.Integer("Eggs laid down", readonly=True, states={'draft': [('readonly', False)]})    
    eggs_weight = fields.Float("Eggs Weight", readonly=True, states={'draft': [('readonly', False)]})
    eggs_dirty = fields.Integer("Dirty Eggs", readonly=True, states={'draft': [('readonly', False)]})
    eggs_broken = fields.Integer("Broken Eggs", readonly=True, states={'draft': [('readonly', False)]})
    
    eggs_color = fields.Selection([(1,"01"),
                                   (2,"02"),
                                   (3,"03"),
                                   (4,"04"),
                                   (5,"05"),
                                   (6,"06"),
                                   (7,"07"),
                                   (8,"08"),
                                   (9,"09"),
                                   (10,"10"),
                                   (11,"11"),
                                   (12,"12"),
                                   (13,"13"),
                                   (14,"14"),
                                   (15,"15"),
                                  ]
                                  , string="Eggs Color", help="Color aligned to the DSM Yolk Color Fan" 
                                  , readonly=True, states={'draft': [('readonly', False)]})
    
    
    eggs_color_dote = fields.Selection([(1,"01"),
                                       (2,"02"),
                                       (3,"03"),
                                       (4,"04"),
                                       (5,"05"),
                                       (6,"06"),
                                       (7,"07"),
                                       (8,"08"),
                                       (9,"09"),
                                       (10,"10"),
                                       (11,"11"),
                                       (12,"12"),
                                       (13,"13"),
                                       (14,"14"),
                                       (15,"15"),
                                      ]
                                      , string="Eggs Dote Color", help="Color aligned to the DSM Yolk Color Fan"
                                      , readonly=True, states={'draft': [('readonly', False)]}) 
    
    eggs_thickness = fields.Float("Eggs Thickness", readonly=True, states={'draft': [('readonly', False)]})
    
    state = fields.Selection([("draft","Draft"),
                              ("valid","Valid"),
                              ("invalid","Invalid")],
                              string="State", default="draft")
      