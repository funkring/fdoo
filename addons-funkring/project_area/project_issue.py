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

from openerp.osv import osv

class project_issue(osv.osv):
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(project_issue,self).default_get(cr,uid,fields_list,context=None)
        if context and context.get("project_area") and "partner_id" in fields_list:
            partner = self.pool.get("res.users").browse(cr,uid,uid,context).partner_id
            if partner:
                res["partner_id"]=partner.id
        return res
     
    _inherit = "project.issue"
    
    
project_issue()