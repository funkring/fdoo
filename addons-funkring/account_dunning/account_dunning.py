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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.addons.at_base import util
from dateutil.relativedelta import relativedelta

class dunning_profile(osv.Model):
    _name = "account.dunning_profile"
    _rec_name="name"
    _columns = {
        "line_ids" : fields.one2many("account.dunning_profile_line", "profile_id", "Profile lines"),
        "company_id" : fields.many2one("res.company", "Company", required=True),
        "name" : fields.related("company_id", "name", string="Name")
    }
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.dunning_profile', context=c),
    }
    
class dunning_profile_line(osv.Model):
    
    def line_next(self,cr,uid,profile,profile_line,date_current,date_due):
        if not date_due:
            return None
        date_current = util.strToDate(date_current)
        date_due = util.strToDate(date_due)        
        #check if profile 
        if profile_line and profile_line.profile_id.id != profile.id:
            profile_line=None            
        #calc next line
        delta = date_current-date_due        
        line_next = None
        #
        if ( delta.days > 0 ):            
            profile_line_obj = self.pool.get("account.dunning_profile_line")
            lines = profile_line_obj.browse(cr,uid,profile_line_obj.search(cr,uid,[("profile_id","=",profile.id)],order="sequence asc"))
            for line in lines:
                remind_date = date_due+relativedelta(days=line.delay)
                if remind_date <= date_current:
                    line_next = line
                    if not profile_line or line_next.sequence > profile_line.sequence:
                        break            
        return line_next
    
    _name = "account.dunning_profile_line"
    _columns = {
        "name" : fields.char("Name", size=64, required=True),
        "sequence" : fields.integer("Sequence", help="It helps to order the profile lines"),
        "delay" : fields.integer("Days of delay"),
        "profile_id" : fields.many2one("account.dunning_profile", "Profile", required=True, ondelete="cascade"),
        "dunning_fee_percent" : fields.boolean("Dunning Fee %"),
        "dunning_fee" : fields.float("Dunning Fee", digits_compute=dp.get_precision("Account")),
        "description" : fields.text("Text before", translate=True),
        "description2" : fields.text("Text after", translate=True)
    }
    
    
    