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
from datetime import datetime

class chicken_logbook(models.Model):
    
    @api.one
    def action_start(self):
        if self._get_active(self.house_id.id):
            raise Warning(_("Only one active logbook per house allowed!"))
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
    def action_inactive(self):
        return self.write({"state":"inactive"})
    
    @api.multi
    def name_get(self):
        result = []
        for book in self:
            result.append((book.id, "%s / %s" % (book.house_id.name,book.name)))
        return result
    
    @api.model
    def _default_name(self):
        return self.env["ir.sequence"].get("farm.chicken.logbook") or "/"
    
    @api.model
    def _get_active(self, house_id):
        res = self.search([("house_id","=",house_id),("state","=","active")],limit=1)
        return res and res[0] or None
    
    @api.model
    def import_logs(self, house_id, data):
        logbook = self._get_active(house_id)
        if not logbook:
            raise Warning(_("No active logbook for house %s") % house_id)
        
        log_obj = self.env["farm.chicken.log"]
        for day, values in data.iteritems():
            log = log_obj.search([("logbook_id","=",logbook.id),("day","=",day)],limit=1)
            log = log and log[0] or None
            
            if not log:
                values["day"]=day
                values["logbook_id"]=logbook.id
                log = log_obj.create(values)
            elif log.state == "draft":
                if log.feed_manual:
                    values.pop("feed")
                log.write(values)
        return True
    
    @api.one
    @api.depends("chicken_age")
    def _compute_chicken_age_weeks(self):
        self.chicken_age_weeks = self.chicken_age / 7.0 
                             
    
    _name = "farm.chicken.logbook"
    _description = "Logbook"
    _inherit = ["mail.thread"]
    _order = "date_start desc"
    
    name = fields.Char("Name", required=True, default=_default_name)
    date_start = fields.Date("Start", required=True, index=True, readonly=True, states={'draft': [('readonly', False)]})
    date_end = fields.Date("End", index=True, readonly=True)
    house_id = fields.Many2one("farm.house", string="House", index=True, required=True, readonly=True, states={'draft': [('readonly', False)]})
    chicken_count = fields.Integer("Chicken Count", readonly=True, states={'draft': [('readonly', False)]})
    chicken_age = fields.Integer("Chicken Age [Days]", help="Chicken age in days", readonly=True, states={'draft': [('readonly', False)]})
    chicken_age_weeks = fields.Integer("Chicken Age [Weeks]", help="chicken age in weeks", readonly=True, compute="_compute_chicken_age_weeks")
    log_ids = fields.One2many("farm.chicken.log", "logbook_id", "Logs")
    state = fields.Selection([("draft","Draft"),
                              ("active","Active"),
                              ("inactive","Inactive"),
                              ("done","Done")],string="State", index=True, default="draft")
        
               
class chicken_log(models.Model):

    @api.one
    def _parent_log(self):
        parent_house = self.logbook_id.house_id.parent_id
        if parent_house:
            parent_logs = self.search([("logbook_id.house_id","=",parent_house.id),("day","=",self.day)])
            return parent_logs and parent_logs[0] or None
            
    
    @api.multi
    def action_draft(self):
        return self.write({"state":"draft"})
        
    @api.one
    def _validate_inv(self):
        # get childs
        parent = self.parent_id
        if not parent:
            parent = self
        logs = [parent]
        logs.extend(parent.child_ids)
        
        # get invoice logs
        inv_logs = []
        non_inv_logs = []
        inv_parent = False
        delivered = False
        for log in logs:
            if log.delivered:
                delivered = True
            if log.inv_exists:
                inv_logs.append(log)
                if log.id == parent.id:
                    inv_parent = True
            else:
                non_inv_logs.append(log)
        
        # check if invoice exist
        if inv_logs:
            for inv_log in inv_logs:
                inv_log.inv_hierarchy = True
                
            # check if parent has no invoice
            if not inv_parent:
                # sumup invoice fields
                inv_fields = {}
                for inv_field in self._inv_fields:
                    val = inv_logs[0][inv_field]
                    for inv_log in inv_logs[1:]:
                        val+=inv_log[inv_field]                    
                    inv_fields[inv_field] = val
                
                # set it to parent
                for inv_field,val in inv_fields.iteritems():
                    parent[inv_field] = val
                    
                if delivered:
                    parent.delivered=delivered 
                    
#             else:
#                 if non_inv_logs:
#                     # calc rest
#                     inv_fields = {}
#                     inv_logs.remove(parent)
#                     for inv_field in self._inv_fields:
#                         val = parent[inv_field]
#                         for inv_log in inv_logs:
#                             val-=inv_log[inv_field]                    
#                         inv_fields[inv_field] = val
#                     
#                     for inv_field in self._inv_fields:
#                         for log in non_inv_logs:
                    
        else:
            for log in logs:
                log.inv_hierarchy = False
        
        return True
            
    @api.multi
    def action_validate(self):
        for log in self:
            log._validate_inv()
            logs_after = log.search([("logbook_id","=",self.logbook_id.id),("day",">",self.day)])
            logs_after._validate_inv()
        return self.write({"state":"valid"})
    
    @api.one
    @api.depends("loss","loss_fix","loss_fix_amount")
    def _compute_loss_total(self):
        # add loss without fix
        self._cr.execute("SELECT SUM(COALESCE(loss,0)) FROM farm_chicken_log l "
                         " WHERE l.logbook_id = %s AND l.day <= %s AND NOT l.loss_fix ", (self.logbook_id.id, self.day) )
        res = self._cr.fetchone()
        loss_total = res and res[0] or 0
        
        # add loss with fix
        self._cr.execute("SELECT SUM(COALESCE(loss_fix_amount,0)) FROM farm_chicken_log l "
                         " WHERE l.logbook_id = %s AND l.day <= %s AND l.loss_fix ", (self.logbook_id.id, self.day) )
        res = self._cr.fetchone()
        loss_total += res and res[0] or 0
        
        self.loss_total = loss_total
        
    @api.one
    @api.depends("loss")
    def _compute_loss_total_real(self):
        self._cr.execute("SELECT SUM(COALESCE(loss,0)) FROM farm_chicken_log l "
                         " WHERE l.logbook_id = %s AND l.day <= %s ", (self.logbook_id.id, self.day) )
        res = self._cr.fetchone()
        loss_total = res and res[0] or 0
        
        self.loss_total_real = loss_total
        
    @api.one
    @api.depends("loss_total_real")
    def _compute_chicken_count(self):
        self.chicken_count = self.logbook_id.chicken_count-self.loss_total_real
        
    @api.one
    @api.depends("eggs_total","eggs_removed")
    def _compute_eggs_count(self):        
        self._cr.execute("SELECT SUM(COALESCE(eggs_total,0))-SUM(COALESCE(eggs_removed,0))-(SUM(COALESCE(delivered_eggs_mixed,0))+SUM(COALESCE(delivered_eggs_industry,0))) FROM farm_chicken_log l "
                         " WHERE l.logbook_id = %s AND l.day <= %s ",
                         (self.logbook_id.id, self.day) )
        res = self._cr.fetchone()
        self.eggs_count = res and res[0] or None
          
    @api.one
    @api.depends("delivered_eggs_mixed",
                 "delivered_eggs_industry",
                 "inv_eggs_xl",
                 "inv_eggs_m",
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
                
    @api.one
    @api.depends("logbook_id.date_start","logbook_id.chicken_age")
    def _compute_chicken_age(self):
        logbook = self.logbook_id
        dt_start = util.strToDate(logbook.date_start)
        dt_cur = util.strToDate(self.day)
        diff = dt_cur - dt_start
        self.chicken_age = logbook.chicken_age + diff.days
        self.chicken_age_weeks = self.chicken_age / 7.0 
    
    @api.one
    @api.depends("eggs_total","chicken_count")    
    def _compute_eggs_performance(self):
        if self.chicken_count:
            self.eggs_performance = float(self.eggs_total) / float(self.chicken_count) * 100
        else:
            self.eggs_performance = 0.0
    
    @api.model
    def _default_logbook_id(self):        
        logbooks = self.env["farm.chicken.logbook"].search([("state","=","active")])
        default_day = util.currentDate()
        for logbook in logbooks:
            logs = self.search([("logbook_id","=",logbook.id),("day","=",default_day)])
            if not logs:                
                return logbook.id            
        return None
    
    @api.one
    @api.depends("day",
                 "logbook_id",
                 "logbook_id.house_id",
                 "logbook_id.house_id.parent_id")
    def _compute_parent_id(self):
        parent_log = None
        parent_house = self.logbook_id.house_id.parent_id
        
        if parent_house:
            parent_log = self.search([("day","=",self.day),
                               ("logbook_id.state","=","active"),
                               ("logbook_id.house_id","=",parent_house.id)])
            # create parent if not exist
            if not parent_log:
                logbook_obj = self.env["farm.chicken.logbook"]
                parent_logbook = logbook_obj._get_active(parent_house.id)
                if parent_logbook:
                    parent_log = self.create({
                            "logbook_id" : parent_logbook.id,
                            "day" : self.day
                          })
            # use existing
            else:
                parent_log = parent_log[0]
        self.parent_id = parent_log
        
    @api.one
    def _validate(self, values=None):
        parent = self.parent_id
        if parent:
            # check for validate
            if values:
                validate_fields = []            
                for field in self._forward_fields:
                    if field in values:
                        validate_fields.append(field)
            else:
                validate_fields = self._forward_fields

            # validate fields                
            if validate_fields:
                childs = parent.child_ids
                if childs:
                    values = self.read(validate_fields)[0]
                    for key in validate_fields:
                        val = values[key]
                        for child in childs:
                            if child.id == self.id:
                                continue
                            val += child[key]
                        values[key]=val
                    parent.write(values)
                    
    def _create(self, cr, uid, vals, context=None):
        res = super(chicken_log,self)._create(cr, uid, vals, context=context)
        self.browse(cr, uid, res, context=context)._validate(vals)
        return res
                
    def _write(self, cr, uid, ids, vals, context=None):
        res = super(chicken_log,self)._write(cr, uid, ids, vals, context=context)        
        self.browse(cr, uid, ids, context=context)._validate(vals)
        return res
    
    _name = "farm.chicken.log"
    _description = "Log"
    _inherit = ["mail.thread"]
    _order = "day desc, logbook_id"
    _rec_name = "day"
    
    _forward_fields = [
        "loss",
         "feed",
         "water",                 
         "eggs_total",
         "eggs_nest",
         "eggs_top",
         "eggs_buttom",
         "eggs_dirty",
         "eggs_broken",
         "eggs_removed"      
    ]
    _inv_fields = [
         "delivered_eggs_mixed",
         "delivered_eggs_industry",
         "inv_eggs_xl",
         "inv_eggs_m",
         "inv_eggs_l",
         "inv_eggs_s",
         "inv_eggs_s45g",
         "inv_eggs_industry",
         "inv_eggs_presorted"     
    ]
    
    _sql_constraints = [
        ("date_uniq", "unique(logbook_id, day)",
            "Only one log entry per day allowed!")
    ]
    
    logbook_id = fields.Many2one("farm.chicken.logbook","Logbook",required=True, index=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=_default_logbook_id, ondelete="restrict")
    
    day = fields.Date("Day", required=True, readonly=True, index=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: util.currentDate())
    
    loss = fields.Integer("Loss", readonly=True, states={'draft': [('readonly', False)]})
    loss_fix = fields.Boolean("Loss Fix", readonly=True, states={'draft': [('readonly', False)]})
    loss_fix_amount = fields.Integer("Loss Fix Amount", readonly=True, states={'draft': [('readonly', False)]})
    loss_total = fields.Integer("Loss Total", readonly=True, compute="_compute_loss_total")
    loss_total_real = fields.Integer("Real Loss", readonly=True, compute="_compute_loss_total_real")
    
    weight = fields.Float("Weight [kg]", readonly=True, states={'draft': [('readonly', False)]})
    feed_manual = fields.Boolean("Manual Feed Input", readonly=True, states={'draft': [('readonly', False)]})
    feed = fields.Float("Feet [kg]", readonly=True, states={'draft': [('readonly', False)]})
    water = fields.Float("Water [l]", readonly=True, states={'draft': [('readonly', False)]})
    co2 = fields.Float("Co2", readonly=True, states={'draft': [('readonly', False)]})
    temp = fields.Float("Temperature [°C]", readonly=True, states={'draft': [('readonly', False)]})
    humidity = fields.Float("Humidity [%]", readonly=True, states={'draft': [('readonly', False)]})
    eggs_total = fields.Integer("Eggs Total", readonly=True, states={'draft': [('readonly', False)]})
    eggs_machine = fields.Integer("Eggs Machine", readonly=True, states={'draft': [('readonly', False)]})
    
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
                                       (5,"05")
                                      ]
                                      , string="Eggs Dote Color", help="Color aligned to the DSM Yolk Color Fan"
                                      , readonly=True, states={'draft': [('readonly', False)]}) 
    
    eggs_thickness = fields.Float("Eggs Thickness [kg]", readonly=True, states={'draft': [('readonly', False)]})
    
    state = fields.Selection([("draft","Draft"),
                              ("valid","Valid"),
                              ("done","Done")],
                              string="State", default="draft")
    
    eggs_removed = fields.Integer("Eggs Removed", readonly=True, states={'draft': [('readonly', False)]}) 
    
    chicken_age = fields.Integer("Chicken Age [Days]", readonly=True, compute="_compute_chicken_age", store=True)
    chicken_age_weeks = fields.Integer("Chicken Age [Weeks]", readonly=True, compute="_compute_chicken_age", store=True)
    chicken_count = fields.Integer("Chicken Count", readonly=True, compute="_compute_chicken_count", store=True)
    eggs_count = fields.Integer("Eggs Stock", readonly=True, compute="_compute_eggs_count")
    eggs_performance = fields.Float("Eggs Performance", readonly=True, compute="_compute_eggs_performance", store=True)
    
    delivered = fields.Boolean("Delivery", readonly=True, states={'draft': [('readonly', False)]})    
    delivered_eggs_mixed = fields.Integer("Delivered Eggs", readonly=True, states={'draft': [('readonly', False)]})
    delivered_eggs_industry = fields.Integer("Delivered Eggs Industry", readonly=True, states={'draft': [('readonly', False)]})
    delivered_eggs = fields.Integer("Delivered Eggs Total", readonly=True, compute="_compute_delivery", store=True)
    
    inv_exists = fields.Boolean("Invoice Exists", help="Standalone invoice for the delivery exists", states={'draft': [('readonly', False)]})
    inv_hierarchy = fields.Boolean("Invoice in Hierarchy Exists")
    inv_eggs_xl = fields.Integer("Invoiced Eggs XL", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_l = fields.Integer("Invoiced Eggs L", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_m = fields.Integer("Invoiced Eggs M", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_s = fields.Integer("Invoiced Eggs S", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_s45g = fields.Integer("Invoiced Eggs < 45g", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_industry = fields.Integer("Invoiced Eggs Industry", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs_presorted = fields.Integer("Invoiced Eggs Industry (presorted)", readonly=True, states={'draft': [('readonly', False)]})
    inv_eggs = fields.Integer("Invoiced Eggs Total", readonly=True, compute="_compute_delivery", store=True)
    
    inv_diff_eggs = fields.Integer("Eggs Difference", readonly=True, compute="_compute_delivery", store=True)
    inv_diff_presorted = fields.Integer("Eggs Difference (presorted)", readonly=True, compute="_compute_delivery", store=True)
    
    child_ids = fields.One2many("farm.chicken.log", "parent_id", string="Child Logs", readonly=True)
    parent_id = fields.Many2one("farm.chicken.log", string="Parent Log", compute="_compute_parent_id", readonly=True, store=True)
