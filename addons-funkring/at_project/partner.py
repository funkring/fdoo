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
    
    def _project_user_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)        
        for oid in ids:
            res[oid]=[]
            
        partner_ids = tuple(ids)
        cr.execute("SELECT a.partner_id AS partner_id, mem.uid AS uid FROM res_users AS u " 
                   "  INNER JOIN account_analytic_account AS a ON a.partner_id = u.partner_id AND a.partner_id IN %s "  
                   "  INNER JOIN project_project AS p ON p.analytic_account_id = a.id "
                   "  INNER JOIN project_user_rel AS mem ON mem.project_id = p.id "                   
                   "  GROUP BY 1,2 "
                   " UNION "
                   "  SELECT a.partner_id AS partner_id, u.id AS uid FROM res_users AS u "  
                   "   INNER JOIN account_analytic_account AS a ON a.partner_id = u.partner_id AND a.partner_id IN %s "
                   "   GROUP BY 1,2 "
                   " UNION "
                   "  SELECT a.partner_id AS partner_id, t.user_id AS uid FROM res_users AS u "  
                   "   INNER JOIN account_analytic_account AS a ON a.partner_id = u.partner_id AND a.partner_id IN %s "
                   "   INNER JOIN project_project AS p ON p.analytic_account_id = a.id "
                   "   INNER JOIN project_task AS t ON t.project_id = p.id "
                   "   GROUP BY 1,2 "
                   " UNION "
                   "   SELECT a.partner_id AS partner_id, a.user_id AS uid FROM res_users AS u "  
                   "   INNER JOIN account_analytic_account AS a ON a.partner_id = u.partner_id AND a.partner_id IN %s "
                   " UNION "
                   "   SELECT u.partner_id AS partner_id, u.id AS uid FROM res_users AS u "
                   "   WHERE u.partner_id IN %s "                   
                   ,(partner_ids,partner_ids,partner_ids,partner_ids,partner_ids))
                                     
        for row in cr.fetchall():
            if row[1]:
                res[row[0]].append(row[1])        
        return res
    
    
    _inherit = "res.partner"    
    _columns = {
        "project_user_ids" : fields.function(_project_user_ids,type="many2many",relation="res.users",readonly=True,string="Project Users")
    }
