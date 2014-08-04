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

from openerp.osv import osv

class res_partner(osv.Model):    
    
    def on_change_zip(self, cr, uid, ids, zip_code, city):
        res = { "value" : {} }
        if not city:
            city_obj = self.pool.get("res.city")
            city_ids = city_obj.search(cr,uid,[("code","=",zip_code)])
            if len(city_ids):
                city = city_obj.browse(cr,uid,city_ids[0])
                res["value"]["city"] = city.name                
                if city.state_id:
                    res["value"]["state_id"] = city.state_id.id
                    res["value"]["country_id"] = city.state_id.country_id.id
        return res
    
    _inherit = "res.partner"