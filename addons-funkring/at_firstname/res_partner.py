#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martinr@funkring.net>
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
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(res_partner, self).default_get(cr, uid, fields_list, context)
        name = res.get("name")
        if name:
            surname, firstname = self._split_name(name)
            
            if "firstname" in fields_list and not res.get("firstname") and firstname:
                res["firstname"] = firstname
                
            if "surname" in fields_list and not res.get("surname") and surname:
                res["surname"] = surname
             
        return res
    
    _inherit = "res.partner"
    _columns = {
      "is_person": fields.boolean("Person")
    }


