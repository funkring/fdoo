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

from openerp.osv import osv,fields

class res_partner(osv.osv):        
    
    def _employee(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
                
        cr.execute("SELECT p.id, e.id FROM res_partner p"
                       " INNER JOIN hr_employee e ON e.address_home_id = p.id "
                       " WHERE p.id IN %s ",(tuple(ids),) )
        
        rows = cr.fetchall()
        for row in rows:
            res[row[0]]= row[1]
        return res
    
    
    _inherit = "res.partner"   
    _columns = {               
         "employee_id" : fields.function(_employee, string="Employee",type="many2one",obj="hr.employee")      
    }
