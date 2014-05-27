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
import uuid

class res_mapping(osv.Model):

    def _browse_mapped(self, cr, uid, uuid, name=None, context=None):
        if uuid:
            uuid_id = self.search_id(cr, uid, [("name","=",name),("uuid","=",uuid)])
            if uuid_id:
                values = self.read(cr, uid, uuid_id, ["res_model","res_id"], context=context)
                res_model = values.get("res_model")
                res_id = values.get("res_id")
                if res_model and res_id:
                    model_obj = self.pool.get(res_model)
                    if model_obj:
                        return model_obj.browse(cr, uid, res_id, context=context)
        return None
    
    def get_uuid(self, cr, uid, res_model, res_id, uuid=None, name=None):        
        uuid_id = self.search_id(cr, uid, [("name","=",name),("res_model","=",res_model),("res_id","=",res_id)])
        if not uuid_id:
            uuid_id = self.create(cr, uid, {"name" : name, "res_model" : res_model, "res_id" : res_id})
        return self.read(cr, uid, uuid_id, ["uuid"])["uuid"]
    
    def get_id(self, cr, uid, res_model, res_uuid, name=None):
        uuid_id =  self.search_id(cr, uid, [("name","=",name),("res_model","=",res_model),("uuid","=",res_uuid)])
        if not uuid_id:
            return None
        return self.read(cr, uid, uuid_id, ["res_id"])["res_id"]
    
    def unlink_uuid(self, cr, uid, uuids, name=None, context=None):
        if isinstance(uuids, basestring):
            uuids = [uuids]
        
        deactivate_ids = []
        for uuid in uuids:
            uuid_id = self.search_id(cr, uid, [("name","=",name),("uuid","=",uuid)])
            if uuid_id:
                deactivate_ids.append(uuid_id)
                values = self.read(cr, uid, uuid_id, ["res_model","res_id"], context=context)
                res_model = values.get("res_model")
                res_id = values.get("res_id")
                if res_model and res_id:
                    model_obj = self.pool.get(res_model)
                    if model_obj:
                        model_obj.unlink(cr, uid, res_id, context=context)
                        
        self.write(cr, uid, deactivate_ids, {"active" : False}, context=context)                        
        return True
        
    
    _name = "res.mapping"
    _columns = {
        "name" : fields.char("Type", size=64, select=True),
        "res_model" : fields.char("Model", size=64, select=True),
        "res_id" : fields.integer("ID", select=True),
        "uuid" : fields.char("UUID", size=64, select=True),
        "active" : fields.boolean("Active",select=True)
    }
    
    _defaults = {
       "uuid" : lambda self,cr,uid,context: uuid.uuid4().hex,
       "active" : True
    }