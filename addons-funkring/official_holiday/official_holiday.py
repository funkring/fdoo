# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

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

from openerp.osv import fields,osv
from openerp.addons.at_base import util

class official_holiday_template(osv.osv):
    
    _name = "official.holiday.template"
    _description = "Official Holiday Template"
    _columns = {
        "name" : fields.char("Name", size=64),
        "official_holiday_ids" : fields.one2many("official.holiday", "template_id", "Holidays")
    }


class official_holiday(osv.osv):
            
    def create_calendar_entries(self, cr, uid, ids, fiscalyear_id, company_id=None, calendar_id=None,
                                  resource_id=None, context=None):
        leave_obj = self.pool.get("resource.calendar.leaves")
        event_obj = self.pool.get("calendar.event")
        account_fiscalyear_obj = self.pool.get("account.fiscalyear")
        fiscal_year_date =  util.strToDate(account_fiscalyear_obj.browse(cr,uid,fiscalyear_id,context).date_start)
        easter_sunday_date = util.dateEasterSunday(fiscal_year_date.year)
                
        for holiday in self.browse(cr, uid, ids, context):
            leave_ids = leave_obj.search(cr, uid, [("official_holiday_id", "=", holiday.id)])
            holiday_date = util.strToDate(holiday.date)
            if holiday.calc_type == "none":
                holiday_date=holiday_date.replace(year=fiscal_year_date.year)
            elif holiday.calc_type == "easter":
                holiday_easter_sunday_date = util.dateEasterSunday(holiday_date.year)
                easter_delta = holiday_easter_sunday_date-easter_sunday_date
                holiday_date = holiday_date+abs(easter_delta)
            if not leave_ids:            
                leave_values = {
                    "name" : holiday.name,
                    "date_from" : util.timeToStr(holiday_date),
                    "date_to" : util.timeToStr(util.getLastTimeOfDay(holiday_date)),
                    "resource_id" : resource_id,
                    "company_id" : company_id,
                    "calendar_id" : calendar_id,
                    "official_holiday_id" : holiday.id
                }
                leave_obj.create(cr,uid, leave_values,context=context)
            event_ids = event_obj.search(cr, uid, [("official_holiday_id", "=", holiday.id)])
            if not event_ids:
                event_values=event_obj.onchange_dates(cr,uid,[],util.timeToStr(holiday_date),allday=True,context=context)["value"]
                event_values["name"]=holiday.name
                event_values["class"]="public"
                event_values["user_id"]=None
                event_values["show_as"]="busy"
                event_values["official_holiday_id"]=holiday.id
                event_values["partner_ids"] = None
                event_obj.create(cr, uid, event_values, context=context)
            
    
    _name = "official.holiday"
    _description = "Official Holiday"
    _columns = {
        "template_id" : fields.many2one("official.holiday", "Template", required=True, ondelete="cascade"),
        "name" : fields.char("Name", size=64, translate=True, required=True),
        "date" : fields.date("Date", required=True),
        "calc_type" : fields.selection([("none", "None"), ("easter", "Easter")], string="Calculation type", required=True),
        "leave_ids" : fields.one2many("resource.calendar.leaves","official_holiday_id", "Resource Leaves"),
        "event_ids" : fields.one2many("calendar.event", "official_holiday_id", "Events")
    }
    
    _order = "date, name"

class calendar_event(osv.osv):
    _inherit="calendar.event"
    _columns = {
        "official_holiday_id" : fields.many2one("official.holiday","Holiday",ondelete="cascade")        
    }

class resource_calendar_leaves(osv.osv):
    _inherit = "resource.calendar.leaves"
    _columns = {
        "official_holiday_id" : fields.many2one("official.holiday","Holiday",ondelete="cascade")
    }
    
