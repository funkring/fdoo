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

class res_partner(osv.osv): 
    
    def _project_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        project_obj = self.pool["project.project"]
        for partner in self.browse(cr, uid, ids, context):
            res[partner.id] = project_obj.search(cr, uid, [("partner_id","=",partner.id),("state","=","open")], count=True, context=context)
        return res
       
    _inherit = "res.partner"
    _columns = {
        "property_partner_analytic_account" : fields.property(
                                                string="Analytic Account",
                                                type="many2one",
                                                relation="account.analytic.account"),
                
        "project_count" : fields.function(_project_count, type="integer", string="Project Count")
    }
