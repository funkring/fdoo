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
from openerp import SUPERUSER_ID
from openerp.tools.translate import _

class res_mapping(osv.Model):

    def _get_model(self, cr, uid, uuid, res_model=None, name=None, context=None):
        if uuid:
            # check if model exist
            if not res_model:
                uuid_id = self.search_id(cr, uid, [("uuid","=",uuid)])
                if not uuid_id:
                    return False
                
                res_model = self.read(cr, uid, uuid_id, ["res_model"])["res_model"]
                return res_model            
        return False

    def _browse_mapped(self, cr, uid, uuid, res_model=None, name=None, context=None):
        if uuid:
            # check if model exist
            if not res_model:
                uuid_id = self.search_id(cr, uid, [("uuid","=",uuid)])
                if not uuid_id:
                    raise osv.except_osv(_("Error"), _("No model found for uuid %s" % uuid))
                
                res_model = self.read(cr, uid, uuid_id, ["res_model"])["res_model"]
                if not res_model:
                    raise osv.except_osv(_("Error"), _("No model found for uuid %s" % uuid))
            
            # get id
            res_id = self.get_id(cr, uid, res_model, uuid, name=name)
            if res_id:
                return self.pool[res_model].browse(cr, uid, res_id, context=context)
            
        return False

    def get_uuid(self, cr, uid, res_model, res_id, uuid=None, name=None, locked=False):
        uuid_id = self.search_id(cr, uid, [("name","=",name),("res_model","=",res_model),("res_id","=",res_id)])
        if not uuid_id:
            if uuid:
                uuid_id = self.create(cr, uid, {"name" : name, "res_model" : res_model, "res_id" : res_id, "uuid" : uuid, "locked" : locked})
            else:
                uuid_id = self.create(cr, uid, {"name" : name, "res_model" : res_model, "res_id" : res_id, "locked" : locked})
        
        # read again
        values = self.read(cr, uid, uuid_id, ["uuid","locked"])
        
        # check update for locked state
        if not values["locked"] and locked:
            self.write(cr, uid, uuid_id, {"locked": True})
            
        return values["uuid"]

    def _get_uuid(self, cr, uid, obj, uuid=None, name=None):
        if not obj:
            return None
        return self.get_uuid(cr, uid, obj._model._name, obj.id, uuid, name)

    def get_mapping(self, cr, uid, res_uuid, res_model=None, name=None):
        uuid_id = False
        if not res_model:
            uuid_id = self.search_id(cr, uid, [("name","=",name),("uuid","=",res_uuid)])
        else:
            uuid_id = self.search_id(cr, uid, [("name","=",name),("res_model","=",res_model),("uuid","=",res_uuid)])
            
        if not uuid_id:
            return {
                "res_id": None, 
                "res_model": res_model
            }
        
        values = self.read(cr, uid, uuid_id, ["res_id", "res_model", "locked", "active"])
        res_id = self.pool[res_model].search_id(cr, SUPERUSER_ID, [("id","=",values["res_id"])], context={"active_test":False})
        if not res_id:
            if values["active"]:
                self.write(cr, SUPERUSER_ID, uuid_id, {"active" : False})
            values["active"] = False
            values[res_id] = False
        
        return values
    
    def get_id(self, cr, uid, res_model, res_uuid, name=None):
        uuid_id = False
        if not res_model:
            uuid_id = self.search_id(cr, uid, [("name","=",name),("uuid","=",res_uuid)])
        else:
            uuid_id = self.search_id(cr, uid, [("name","=",name),("res_model","=",res_model),("uuid","=",res_uuid)])
            
        if not uuid_id:
            return False
        
        res_id = self.read(cr, uid, uuid_id, ["res_id"])["res_id"]
        res_id = self.pool[res_model].search_id(cr, SUPERUSER_ID, [("id","=",res_id)], context={"active_test":False})
        if not res_id:
            self.write(cr, SUPERUSER_ID, uuid_id, {"active" : False})
        return res_id

    def unlink_uuid(self, cr, uid, uuids, res_model=None, name=False, context=None):
        if isinstance(uuids, basestring):
            uuids = [uuids]

        deactivate_ids = []
        
        for uuid in uuids:
            # get uuid
            if not res_model:
                uuid_id = self.search_id(cr, uid, [("name","=",name),("uuid","=",uuid)])
            else:
                uuid_id = self.search_id(cr, uid, [("name","=",name),("res_model","=",res_model),("uuid","=",uuid)])
                
            if uuid_id:
                deactivate_ids.append(uuid_id)
        
                values = self.read(cr, uid, uuid_id, ["res_model","res_id"], context=context)
                
                res_model = values.get("res_model")
                res_id = values.get("res_id")
                
                if res_model and res_id:
                    model_obj = self.pool.get(res_model)
                    if model_obj:
                        model_obj.unlink(cr, uid, [res_id], context=context)

        self.write(cr, uid, deactivate_ids, {"active" : False}, context=context)
        return True

    def search_uuid(self, cr, uid, res_model, domain, fields=None, offset=0, limit=None, order=None, context=None, count=False, name=None):
        model_obj = self.pool[res_model]
        res_ids = model_obj.search(cr, uid, domain, offset=offset, limit=limit, order=order, context=context)
        
        if not fields:
            uuids = []
            for res_id in res_ids:
                res_uuid = self.get_uuid(cr, uid, res_model, res_id, name=name)
                uuids.append(res_uuid) 
            
            if count:
                return len(uuids)
            return uuids
        
        values = False
        if not fields:
            values = []
            for res_id in res_ids:
                values.append(self.get_uuid(cr, uid, res_model, res_id, name=name))
        else:
            values = model_obj.read(cr, uid, res_ids, fields, context=context)
            for val in values:
                val["_id"] =  self.get_uuid(cr, uid, res_model, val["id"], name=name)
            
        return values;

    def check_deleted(self, cr, uid, res_model):
        model_obj = self.pool[res_model]
        query =  ("SELECT m.id FROM res_mapping m "
                 " LEFT JOIN %s r ON r.id = m.res_id " 
                 " WHERE m.active=true AND m.res_model = '%s' AND r.id IS NULL ") % (model_obj._table, res_model)
        
        cr.execute(query)
        
        mapping_ids = [r[0] for r in cr.fetchall()]
        if mapping_ids:
            self.write(cr, SUPERUSER_ID, mapping_ids, {"active" : False})
        
        return True
        
        
    _name = "res.mapping"
    _columns = {
        "name" : fields.char("Type", select=True),
        "res_model" : fields.char("Model", select=True),
        "res_id" : fields.integer("ID", select=True),
        "uuid" : fields.char("UUID", select=True),
        "active" : fields.boolean("Active", select=True),
        "locked" : fields.boolean("Locked", select=True)
    }

    _defaults = {
       "uuid" : lambda self,cr,uid,context: uuid.uuid4().hex,
       "active" : True
    }