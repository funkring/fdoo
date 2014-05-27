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

class City(osv.Model): 
    
    def _country_id_get(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT c.id, c.country_id, s.country_id FROM res_city c"
                   " LEFT JOIN res_country_state s ON s.id = c.state_id "
                   " WHERE c.id IN %s", (tuple(ids),))
        for row in cr.fetchall():
            res[row[0]]=row[2] or row[1] or None 
        return res
    
    def _country_id_set(self, cr, uid, oid, field_name, field_value, arg, context=None):
        state_id = self.read(cr, uid, oid, ["state_id"], context=context)["state_id"]
        if not state_id and oid:
            cr.execute("UPDATE res_city SET country_id = %s WHERE id = %s", (field_value,oid)) 
        
    def name_get(self, cr, user, ids, context=None):
        res = []
        country_code_map = {}
        country_obj = self.pool.get("res.country")
        for val in self.read(cr, user, ids, ["name","code","country_id"],context=context):
            name = val["name"]
            oid = val["id"]
            country_id = val["country_id"]
            if not name:
                name_lst = []
                # add country
                if country_id:
                    country_code = country_code_map.get(country_id)
                    if not country_code:
                        country_code  = country_obj.read(cr, user, country_id, ["code"], context=context)["code"]
                        country_code_map[country_id]=country_code
                    if country_code:
                        name_lst.append(country_code)
                #add postal code
                name_lst.append(val["code"])
                res.append((oid,"-".join(name_lst)))
            else:
                res.append(oid,name)
        return res
            
    _name = "res.city"
    _description = "City"
    _columns = {        
        "code" : fields.char("Code",size=24,required=True,select=True),
        "name" : fields.char("Name"),
        "state_id" : fields.many2one("res.country.state","State"),
        "country_id" : fields.function(_country_id_get, fnct_inv=_country_id_set,type="many2one", obj="res.country", store=True,string="Country")
    }       
    
    

