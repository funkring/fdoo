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

class official_holiday_template_wizard(osv.osv):
    
    def do_create(self, cr, uid, ids, context=None):
        holiday_obj = self.pool.get("official.holiday")
        template_obj = self.pool.get("official.holiday.template")
        user_obj = self.pool.get("res.users")
        
        template_ids = template_obj.search(cr,uid,[("id","in",util.active_ids(context))])
        company_id = user_obj.browse(cr, uid, uid, context).company_id.id
        official_holiday_ids = []
        
        for template_id in template_ids:
            template = template_obj.browse(cr, uid, template_id)
            for holiday in template.official_holiday_ids:
                official_holiday_ids.append(holiday.id)
        
        for wizard in self.browse(cr, uid, ids, context=context):
            holiday_obj.create_calendar_entries(cr, uid, official_holiday_ids, fiscalyear_id=wizard.fiscalyear_id.id, company_id=company_id, context=context)
        
        return { "type" : "ir.actions.act_window_close" }
    
    _name = "official.holiday.template.wizard"
    _description = "Official holiday template wizard"
    
    _columns = {
        "fiscalyear_id" : fields.many2one("account.fiscalyear", "Fiscal Year")
    }
    
