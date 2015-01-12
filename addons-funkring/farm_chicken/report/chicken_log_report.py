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

from openerp import tools
from openerp.osv import fields, osv

class farm_chicken_log_report(osv.Model):
    
    _name = "farm.chicken.log.report"
    _description = "Chicken Log Report"
    _auto = False
    _rec_name = 'day'
    _columns = {
        "logbook_id" : fields.many2one("farm.chicken.logbook","Logbook", readonly=True),
        "house_id" : fields.many2one("farm.house","House", readonly=True),
        "day" : fields.date("Day", readonly=True),
        "loss" : fields.integer("Loss", readonly=True),
        "feed" : fields.float("Feet", readonly=True),
        "water" : fields.float("Water", readonly=True),
        "co2" : fields.float("Co2", readonly=True),
        "temp" : fields.float("Temperature [°C]", readonly=True),
        "humidity" : fields.float("Humidity [%]", readonly=True),
        "eggs_total" : fields.integer("Eggs Total", readonly=True),
        "eggs_nest" : fields.integer("Nest Eggs", readonly=True),
        "eggs_top" : fields.integer("Eggs Top", readonly=True),
        "eggs_buttom" : fields.integer("Eggs Buttom", readonly=True),
        "eggs_weight" : fields.float("Eggs Weight [kg]", readonly=True),
        "eggs_dirty" : fields.integer("Dirty Eggs", readonly=True),
        "eggs_broken" : fields.integer("Broken Eggs", readonly=True),
        "eggs_color" : fields.integer("Eggs Color", readonly=True),
        "eggs_color_dote" : fields.integer("Eggs Dote Color", readonly=True),
        "eggs_thickness" : fields.float("Eggs Thickness [kg]", readonly=True),
        "eggs_removed" : fields.integer("Eggs Removed", readonly=True),
        "chicken_age" : fields.integer("Chicken Age [Days]", readonly=True),
        "chicken_age_weeks" : fields.integer("Chicken Age [Weeks]", readonly=True)
    }
    _order = "logbook_id, chicken_age"
    
    def _select(self):
        return """
            SELECT MIN(l.id) AS id,
                   l.logbook_id AS logbook_id,
                   b.house_id AS house_id,
                   MIN(l.day) AS day,
                   SUM(l.loss) AS loss,            
                   SUM(l.feed) AS feed,
                   SUM(l.water) AS water,
                   SUM(l.co2) AS co2,
                   AVG(l.temp) AS temp,
                   AVG(l.humidity) AS humidity,
                   SUM(l.eggs_total) AS eggs_total,
                   SUM(l.eggs_nest) AS eggs_nest,
                   SUM(l.eggs_top) AS eggs_top,
                   SUM(l.eggs_buttom) AS eggs_buttom,
                   SUM(l.eggs_weight) AS eggs_weight,
                   SUM(l.eggs_dirty) AS eggs_dirty,
                   SUM(l.eggs_broken) AS eggs_broken,
                   AVG(l.eggs_color) AS eggs_color,
                   AVG(l.eggs_color_dote) AS eggs_color_dote,
                   AVG(l.eggs_thickness) AS eggs_thickness,
                   SUM(l.eggs_removed) AS eggs_removed,
                   l.chicken_age,
                   l.chicken_age_weeks
        """
        
        
    def _from(self):
        return """
              farm_chicken_log l
              INNER JOIN farm_chicken_logbook b ON b.id = l.logbook_id AND b.state = 'active' 
        """
    
    def _group_by(self):
        return """
            GROUP BY 
                l.logbook_id,
                b.house_id, 
                l.chicken_age,
                l.chicken_age_weeks
        """
        
    def init(self, cr):
        # self._table = sale_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))