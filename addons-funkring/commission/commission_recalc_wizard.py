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

from openerp.osv import fields, osv
from openerp.addons.at_base import util
from openerp.tools.translate import _

class commission_recalc_wizard(osv.osv_memory):
            
    def do_recalc(self, cr, uid, ids, context=None):
        res = self.pool["ir.actions.act_window"].for_xml_id(cr, uid, "commission","action_commission_line", context=context)
        res["clear_breadcrumbs"] = True
        res["display_name"] = _("Commissions")
        return res
    
    def action_calc(self, cr, uid, ids, context=None):
        commission_obj = self.pool["commission.line"]
        for wizard in self.browse(cr, uid, ids, context=context):
            if wizard.remove_existing:
                # filter
                domain = [("company_id","=",wizard.company_id.id),("invoiced_id","=",False)]
                if wizard.date_from:
                    domain.append(("date",">=",wizard.date_from))
                if wizard.date_to:
                    domain.append(("date","<=",wizard.date_to))
                if wizard.user_id:
                    domain.append(("partner_id.user_ids","in",[wizard.user_id.id]))
                # search and remove old commissoin lines
                old_commission_ids = commission_obj.search(cr, uid, domain, context=context)
                commission_obj.unlink(cr, uid, old_commission_ids, context=context)
        # start recalc            
        return self.do_recalc(cr, uid, ids, context=None)
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(commission_recalc_wizard, self).default_get(cr, uid, fields_list, context=None)
        date_from = util.getFirstOfLastMonth()
        if "date_from" in fields_list:
            res["date_from"] = date_from
        if "date_to" in fields_list:
            res["date_to"] = util.getEndOfMonth(date_from)
        if "company_id" in fields_list:
            res["company_id"] = self.pool["res.company"]._company_default_get(cr, uid, "commission.recalc_wizard", context=context)
        return res
    
    _name = "commission.recalc_wizard"
    _description = "Recalculate Commissions"
    _columns = {
        "company_id" : fields.many2one("res.company", "Company", required=True),
        "user_id": fields.many2one("res.users","Salesman"),
        "date_from" : fields.date("Date from", help="The date which you entered is involved!"),
        "date_to" : fields.date("Date to", help="The date which you entered is involved!"),
        "remove_existing" : fields.boolean("Remove existing")
    }    
    
