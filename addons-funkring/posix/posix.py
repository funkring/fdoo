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


class posix_domain(osv.Model):
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = name + "." + record['parent_id'][1]
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):        
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)
    
    _name="posix.domain"
    _description="Domain"
    _columns = {
        "name" : fields.char("Name",size=32),
        'complete_name': fields.function(_name_get_fnc, type="char", string="Name",size=64,store=True),
        "parent_id" : fields.many2one("posix.domain","Parent Domain",select=True,ondelete="restrict"),
        "child_ids" : fields.one2many("posix.domain","parent_id",string="Child Domains"),
        "description" : fields.text("Description")
    }        


class res_user(osv.Model):     
    _inherit = "res.users"
    _columns = {
        "posix" : fields.boolean("Posix User"),
        "posix_domain_id" : fields.many2one("posix.domain","Primary Domain"),       
        "domain_name" : fields.related("posix_domain_id","complete_name",string="Domain",type="char",size=64,store=True)
    }    


class res_group(osv.Model):
    _inherit =  "res.groups"
    _columns = {
        "posix" : fields.boolean("Posix Group"),        
        "posix_domain_id" : fields.many2one("posix.domain","Domain"),
        "domain_name" : fields.related("posix_domain_id","complete_name",string="Domain",type="char",size=64,store=True)        
    }
