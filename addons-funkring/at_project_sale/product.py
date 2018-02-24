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

class product_template(osv.osv):
    _inherit = "product.template"
    _columns = {
        "billed_at_cost" : fields.boolean("Billed at Cost"),
        "planned_hours" : fields.float("Planned Hours"),
        "recurring_invoices" : fields.boolean("Recurring Invoice or Task"),
        
        "recurring_rule_type" : fields.selection([("daily", "Day(s)"),
                                                  ("weekly", "Week(s)"),
                                                  ("monthly", "Month(s)"),
                                                  ("yearly", "Year(s)")], 
                                string="Recurrency", help="Invoice automatically repeat at specified interval"),
                
        "recurring_interval": fields.integer("Repeat Every", help="Repeat every (Days/Week/Month/Year)"),
        "recurring_tmpl_id": fields.many2one("account.analytic.account", "Template of Contract")        
    }
    
    _defaults = {
      "recurring_rule_type": "monthly",
      "recurring_interval": 1
    }