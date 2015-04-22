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

class res_users(osv.Model):
    
    def _eagency_client_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT u.id, c.id FROM res_users u " 
                   " INNER JOIN res_partner p ON p.id = u.partner_id "
                   " INNER JOIN eagency_client c ON c.partner_id = p.id "
                   " WHERE u.id IN %s " 
                   " GROUP BY 1,2 ", (tuple(ids),))
        
        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res
    
    def _relids_eagency_client(self, cr, uid, ids, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT u.id FROM eagency_client c " 
                   " INNER JOIN res_partner p ON p.id = c.partner_id "
                   " INNER JOIN res_users u ON u.partner_id = p.id "
                   " WHERE c.id IN %s " 
                   " GROUP BY 1", (tuple(ids),))
        return [r[0] for r in cr.fetchall()]

    _inherit = "res.users"
    _columns = {
        "eagency_client_id" : fields.function(_eagency_client_id, string="Client", type="many2one", obj="eagency.client", store={
            "eagency.client" : (_relids_eagency_client,["partner_id"],10),
            "res.users": (lambda self, cr, uid, ids, context=None: ids, ["partner_id"],10)
        })
    }