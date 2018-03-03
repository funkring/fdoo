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

from openerp import api
from openerp.osv import fields,osv
from openerp.addons.at_base import util

class project_work(osv.osv):

    def onchange_user(self, cr, uid, ids, date, hours, user_id):
        if uid==user_id:
            ts_obj = self.pool.get("hr_timesheet_sheet.sheet")
            ts_day = ts_obj.get_timesheet_day(cr,uid,util.currentDate())
            if ts_day:
                return {"value" : {"hours" : ts_day.total_difference }}
        return {}
    
    _inherit = "project.task.work"
    

class project(osv.osv):
    
    def name_get(self, cr, uid, ids, context=None):
        res = []
        for project in self.browse(cr, uid, ids, context=context):
            name = project.name or ""
            partner = project.partner_id
            if partner:
                res.append((project.id, "%s [%s]"  % (name, partner.name)))
            else:
                res.append((project.id,name))
        return res
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):        
        res = super(project,self).name_search(cr, uid, name, args=args, operator=operator, context=context, limit=limit)
        if not res:
            project_ids = self.search(cr, uid, [("partner_id.name", operator, name)], limit=limit, context=context)
            if project_ids:
                return self.name_get(cr, uid, project_ids, context=context)
        return res
    
    _inherit = "project.project"
    
    
class task(osv.osv):
    
    @api.cr_uid_ids_context
    def onchange_project(self, cr, uid, id, project_id, context=None):
        res = super(task, self).onchange_project(cr, uid, id, project_id, context=context)
        if project_id:
            project = self.pool.get('project.project').browse(cr, uid, project_id, context=context)
            if project:
                value = res.get("value") or {}
                value["analytic_account_id"] = project.analytic_account_id.id
                res["value"] = value
        return res
    
    _inherit = "project.task"
    _columns = {
        "analytic_account_id" : fields.related("project_id", "analytic_account_id", string="Analytic Account", type="many2one", relation="account.analytic.account", readonly=True),
        "inv_product_id": fields.many2one("product.product", "Invoice Product", help="The product which will be used for timesheet based invoices")
    }

    