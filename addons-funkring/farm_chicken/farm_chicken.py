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
from openerp.addons.at_base import util

class chicken_logbook(models.Model):
    
    @api.multi
    def action_start(self):
        return self.write({"state":"active"})
    
    @api.multi
    def action_draft(self):
        log_obj = self.env["farm.chicken.log"]
        logs = log_obj.search([("logbook_id","in",self.ids)])
        logs.write({"state":"valid"})
        return self.write({"state":"draft"})
    
    @api.multi
    def action_done(self):
        log_obj = self.env["farm.chicken.log"]
        logs = log_obj.search([("logbook_id","in",self.ids),("state","!=","valid")])
        if logs:
            raise Warning(_("There are unvalided logbook entries"))
        
        for log in self:
            self._cr.execute("SELECT MAX(l.day) FROM farm_chicken_log l WHERE l.logbook_id = %s", (log.id,))
            row = self._cr.fetchone()
            if row and row[0]:
                log.write({"date_end":row[0]})
        
        logs = log_obj.search([("logbook_id","in",self.ids),("state","=","valid")])
        logs.write({"state":"done"})
        return self.write({"state":"done"})
    
    @api.multi
    def name_get(self):
        result = []
        for book in self:
            result.append((book.id, "%s / %s" % (book.house_id.name,book.name)))
        return result
    
    @api.model
    def _default_name(self):
        return self.env["ir.sequence"].get("farm.chicken.logbook") or "/"
    
    _name = "farm.chicken.logbook"
    _description = "Logbook"
    _inherit = ["mail.thread"]
    _order = "date_start desc"
    
    name = fields.Char("Name", required=True, default=_default_name)
    date_start = fields.Date("Start", required=True, index=True, readonly=True, states={'draft': [('readonly', False)]})
    date_end = fields.Date("End", index=True, readonly=True)
    house_id = fields.Many2one("farm.house", string="House", index=True, required=True, readonly=True, states={'draft': [('readonly', False)]})
    chicken_count = fields.Integer("Chicken Count")
    chicken_age = fields.Integer("Chicken Age [Weeks]", help="Chicken age in days")
    log_ids = fields.One2many("farm.chicken.log", "logbook_id", "Logs")
    state = fields.Selection([("draft","Draft"),
                              ("active","Active"),
                              ("done","Done")],string="State", index=True, default="draft")
        
               
class chicken_log(models.Model):

    @api.one
    def _validate(self):
        if not self.inv_exists:
            parent_log = self._parent_log()
            if parent_log:
               pass                                          
                
    @api.one
    def _parent_log(self):
        parent_house = self.logbook_id.house_id.parent_id
        if parent_house:
            parent_logs = self.search([("logbook_id.house_id","=",parent_house.id),("day","=",self.day)])
            return parent_logs and parent_logs[0] or None
            
    @api.one
    def validate_dependend(self):        
        house = self.logbook_id.house_id
        
        parent_house = house.parent_id
        root_house = house
        while parent_house:
            root_house = parent_house
            parent_house = house.parent_id 
            
        dependend = self.search([("id","child_of",root_house.id),("day","=",self.day)])
        for log in dependend:
            log._validate()        
    
    @api.multi
    def action_draft(self):
        return self.write({"state":"draft"})
    
    @api.multi
    def action_validate(self):
        #for log in self:
        #    log.validate()
        return self.write({"state":"valid"})
    
    @api.multi
    def action_invalid(self):
        return self.write({"state":"invalid"})
    
    @api.one
    @api.depends("loss")
    def _compute_chicken_count(self):
        self._cr.execute("SELECT SUM(loss) FROM farm_chicken_log l "
                         " WHERE l.logbook_id = %s AND l.day <= %s ", (self.logbook_id.id, self.day) )
        self.chicken_count = self.logbook_id.chicken_count-self._cr.fetchone()[0]
        
    @api.one
    @api.depends("eggs_total","eggs_removed")
    def _compute_eggs_count(self):        
        self._cr.execute("SELECT SUM(eggs_total)-SUM(eggs_removed)-(SUM(delivered_eggs_mixed)+SUM(delivered_eggs_industry)) FROM farm_chicken_log l "
                         " WHERE l.logbook_id = %s AND l.day <= %s ",
                         (self.logbook_id.id, self.day) )
        self.eggs_count = self._cr.fetchone()[0]
          
    @api.one
    @api.depends("delivered_eggs_mixed",
                 "delivered_eggs_industry",
                 "inv_eggs_xl",
                 "inv_eggs_l",
                 "inv_eggs_s",
                 "inv_eggs_s45g",
                 "inv_eggs_industry",
                 "inv_eggs_presorted")
    def _compute_delivery(self):
        self.delivered_eggs = self.delivered_eggs_mixed + self.delivered_eggs_industry
        self.inv_eggs = self.inv_eggs_xl + self.inv_eggs_l + self.inv_eggs_m + self.inv_eggs_s + self.inv_eggs_s45g + self.inv_eggs_industry + self.inv_eggs_presorted
        self.inv_diff_eggs = self.inv_eggs - self.delivered_eggs
        self.inv_diff_presorted = self.inv_eggs_presorted - self.delivered_eggs_industry
                
    @api.model
    def _default_logbook_id(self):        
        logbooks = self.env["farm.chicken.logbook"].search([("state","=","active")])
        default_day = util.currentDate()
        for logbook in logbooks:
            logs = self.search([("logbook_id","=",logbook.id),("day","=",default_day)])
            if not logs:                
                return logbook.id            
        return None
    
    
    _name = "farm.chicken.log"
    _description = "Log"
    _inherit = ["mail.thread"]
    _order = "day desc, logbook_id"
    _rec_name = "day"
    _sql_constraints = [
        ("date_uniq", "unique(logbook_id, day)",
            "Only one log entry per day allowed!")
    ]
    
    logbook_id = fields.Many2one("farm.chicken.logbook","Logbook",required=True, index=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=_default_logbook_id)
    
    day = fields.Date("Day", required=True, readonly=True, index=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: util.currentDate())
    
    loss = fields.Integer("Loss", readonly=True, states={'draft': [('readonly', False)]})    
    weight = fields.Float("Weight [kg]", readonly=True, states={'draft': [('readonly', False)]})
    feed_manual = fields.Boolean("Manual Feed Input", readonly=True, states={'draft': [('readonly', False)]})
    feed = fields.Float("Feet [kg]", readonly=True, states={'draft': [('readonly', False)]})
    water = fields.Float("Water [l]", readonly=True, states={'draft': [('readonly', False)]})
    co2 = fields.Float("Co2", readonly=True, states={'draft': [('readonly', False)]})
    temp = fields.Float("Temperature [°C]", readonly=True, states={'draft': [('readonly', False)]})
    humidity = fields.Float("Humidity [%]", readonly=True, states={'draft': [('readonly', False)]})
    eggs_total = fields.Integer("Eggs Total", readonly=True, states={'draft': [('readonly', False)]})
    eggs_nest = fields.Integer("Nest Eggs", readonly=True, states={'draft': [('readonly', False)]})
    eggs_top = fields.Integer("Eggs moved above", readonly=True, states={'draft': [('readonly', False)]})
    eggs_buttom = fields.Integer("Eggs laid down", readonly=True, states={'draft': [('readonly', False)]})    
    eggs_weight = fields.Float("Eggs Weight [kg]", readonly=True, states={'draft': [('readonly', False)]})
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
    
    eggs_thickness = fields.Float("Eggs Thickness [kg]", readonly=True, states={'draft': [('readonly', False)]})
    
    state = fields.Selection([("draft","Draft"),
                              ("valid","Valid"),
                              ("done","Done")],
                              string="State", default="draft")
    
    eggs_removed = fields.Integer("Eggs Removed", readonly=True, states={'draft': [('readonly', False)]}) 
    
    chicken_count = fields.Integer("Chicken Count", readonly=True, compute="_compute_chicken_count")
    eggs_count = fields.Integer("Eggs Stock", readonly=True, compute="_compute_eggs_count")
    
    delivered = fields.Boolean("Delivery", readonly=True, states={'draft': [('readonly', False)]})    
    delivered_eggs_mixed = fields.Integer("Delivered Eggs", readonly=True, states={'draft': [('readonly', False)]})
    delivered_eggs_industry = fields.Integer("Delivered Eggs Industry", readonly=True, states={'draft': [('readonly', False)]})
    delivered_eggs = fields.Integer("Delivered Eggs Total", readonly=True, compute="_compute_delivery")
    
    inv_exists = fields.Boolean("Invoice Exists", help="Standalone invoice for the delivery exists", states={'draft': [('readonly', False)]})
    inv_eggs_xl = fields.Integer("Invoiced Eggs XL", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_l = fields.Integer("Invoiced Eggs L", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_m = fields.Integer("Invoiced Eggs M", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_s = fields.Integer("Invoiced Eggs S", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_s45g = fields.Integer("Invoiced Eggs < 45g", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_industry = fields.Integer("Invoiced Eggs Industry", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_presorted = fields.Integer("Invoiced Eggs Industry (presorted)", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs = fields.Integer("Invoiced Eggs Total", readonly=True, compute="_compute_delivery")
    
    inv_diff_eggs = fields.Integer("Eggs Difference", readonly=True, compute="_compute_delivery")
    inv_diff_presorted = fields.Integer("Eggs Difference (presorted)", readonly=True, compute="_compute_delivery")
