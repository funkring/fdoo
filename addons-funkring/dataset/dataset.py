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
from openerp.tools.translate import _
#from openerp.tools import ormcache
import uuid
from openerp.tools.cache import ormcache
from collections import OrderedDict


META_ID = "_id"
META_DELETE = "_delete"
META_NAME = "oerp__name"
META_SCHEMA = "oerp__schema"
META_MODEL = "oerp__model"

META_FIELDS = set([
 META_ID,
 META_NAME,
 META_SCHEMA,
 META_MODEL,
 META_DELETE  
])

def is_meta_field(name):
    return name.startswith("_") or name in META_FIELDS

def is_ref(data):
    if not data:
        return None
    ref_fields=0        
    for key in data.keys():
        if key in META_FIELDS:
            ref_fields+=1
    return ref_fields == len(data)

def get_method(model_obj,name):
    try:
        return getattr(model_obj, name)
    except AttributeError:
        return None
    
class DataDefRecursion(Exception):
    pass

class dataset_dataset(osv.Model):
       
    def _parse_field(self, cr, uid, name, data, values=None, field_def=None, schema=None, context=None):
        # check if it is a meta field
        if is_meta_field(name):
            return None
         
        field_obj = self.pool.get("dataset.field")
        # determine oid
        oid = values.pop("id",None)
        if not oid:
            dataset_id = values.get("dataset_id")
            if dataset_id:
                oid = field_obj.search_id(cr, uid, [("dataset_id","=",dataset_id),("name","=",name)])
 
        if not data is None:
            if values is None:
                values = {}
            if field_def is None:
                field_def = {}
            if context is None:
                context = {}

            values["name"]=name
            dtype = field_def.get("dtype") 
            if not dtype:
                ptype = type(data)                    
                if ptype in (list,tuple):
                    dtype="l"
                elif ptype == bool:
                    dtype="b"
                elif ptype in (int,long):
                    dtype="i"
                elif ptype == float:
                    dtype="f"
                elif isinstance(data,basestring):
                    dtype="s"
                elif isinstance(data,dict):
                    dtype=is_ref(data) and "r" or "c"
                else:
                    raise osv.except_osv(_("Error!"), _("No mapping for type %s") % (ptype,))
               
            values["dtype"]=dtype
            cdataset_id = None
            
            if dtype == "s":
                values["value"]=data
            if dtype == "b":
                values["value_int"]=data and 1 or 0
            if dtype == "f":
                values["value_float"]=data
            if dtype == "i":
                values["value_int"]=data
            if dtype == "t":
                values["value_text"]=data
            if dtype == "l":
                values["child_ids"]=[(6,0,[])]
            if dtype == "r":
                values["value"]=self._data_write(cr, uid, data, return_uuid=True, context=context)
            if dtype == "c":
                if oid:
                    cdataset_id = self.search_id(cr, uid, [("cfield_id","=",oid)]) 
        
            # write current     
            if oid:
                field_obj.write(cr, uid, oid, values, context=context)
            # create new one
            if not oid:                
                oid=field_obj.create(cr, uid, values, context=context)
            
            # parse list entries
            if dtype=="c":
                cdataset_values = {"cfield_id" : oid, 
                                   "id" : cdataset_id }
                self._data_write(cr, uid, data, return_id=True, values=cdataset_values, context=context)
            elif dtype=="l":
                index = 0
                for list_value in data:
                    index_str = name and "%s.%s" % (name,index) or str(index)
                    self._parse_field(cr, uid, index_str, list_value, values={ "parent_id" : oid, "sequence" : index }, 
                                      schema=field_def.get("schema"), context=context)
                    index+=1
        elif oid:
            field_obj.write(cr, uid, oid, { "value" : None, 
                                            "value_int" : None,
                                            "value_text" : None,
                                            "value_float" : None,
                                            "value_id" : None }, context=context)
            
        return oid
    
    def _data_write(self, cr, uid, data, schema=None, values=None, return_id=False, return_uuid=False, context=None):
        # get names
        name = data.get(META_NAME) or schema 
        schema = schema or name
        
        # get definitions
        datas_def = self.pool.get("dataset.view").data_def(cr,uid,"dataset.dataset",schema=schema,context=context) 
        field_defs = datas_def["fields"]

        # setup values        
        if not values:
            values = {}
        if name:
            values["name"]=name
            
        # get id
        oid = values.pop("id",None)
        if not oid:
            # check if exist (with uuid)
            uuid = data.get(META_ID)
            if uuid:
                values["uuid"] = uuid 
                oid = self.search_id(cr, uid, [("uuid","=",uuid),("parent_id","=",False)])
            
        # create new one
        if not oid:
            oid = self.create(cr,uid,values,context=context)  
        else:
            self.write(cr,uid,oid,values,context=context)
        
        for field_name,field_data in data.items():
            field_def = field_defs.get(field_name)
            self._parse_field(cr, uid, field_name, field_data, values={ "dataset_id" : oid }, field_def=field_def, context=context)
        
        if return_id:
            return oid
        
        if not uuid:
            uuid=self.read(cr, uid, oid, ["uuid"],context)["uuid"]
        
        if return_uuid:
            return uuid
            
        res = {
            META_ID : uuid,
            META_MODEL : "dataset.dataset",
        }
        if schema:
            res[META_SCHEMA]=schema   
        return res
    
    def _read_field(self, cr, uid, field, context=None):
        res = None
        
        field_obj = self.pool.get("dataset.field")
        if field.dtype in ("r","c"):
            res = self._data_read(cr, uid, 
                                  field_obj._value(cr,uid,field), 
                                  refonly=(field.dtype=="r"), 
                                  context=context )
        elif field.dtype=="l":
            res=[]
            for child in field.child_ids:
                res.append(self._read_field(cr, uid, child, context))
        else:
            res = field_obj._value(cr,uid,field)

        return res

    def _data_read(self, cr, uid, obj, schema=None, refonly=False, context=None):
        if not obj:
            return None
        res = { META_MODEL : "dataset.dataset" }
        if schema:
            res[META_SCHEMA] = schema
        
        # check if it is a composition
        if not obj.cfield_id:
            res[META_ID]=obj.uuid
            if refonly:
                return res
        elif refonly:
            raise osv.except_osv(_("Error!"), _("Cannot return reference for composition for id %s") % (obj.id,))
        
        name = obj.name
        if name:
            res[META_NAME]=name
            
        for field in obj.field_ids:
            res[field.name]=self._read_field(cr, uid, field, context)
            
        return res
    
    def _version(self, cr, uid, ids, field_names, arg, context=None):
        res = dict.fromkeys(ids)        
        for rec in self.read(cr,uid,ids,["uuid"],context=context):            
            res[rec["id"]] = self.search(cr, uid, [("uuid","=",rec["uuid"])])
        return res
    
    def _update_uuid(self, cr, uid, oid, context=None):
        values = self.read(cr,uid,oid,["uuid","parent_id","cfield_id"],context=context)
        if values["cfield_id"]:
            return True

        uuid = values["uuid"]
        parent_id = values["parent_id"]
        mapping_obj = self.pool.get("res.mapping")
        uuid_id = None
        if not parent_id: #check if it is current version
            uuid_id = mapping_obj.search_id(cr, uid, [("name","=",None),("uuid","=",uuid),("res_model","=","dataset.dataset"),("res_id","=",oid)])
            if not uuid_id:  # if not found if another is linked to uid
                uuid_id = mapping_obj.search_id(cr, uid, [("uuid","=",uuid),("res_model","=","dataset.dataset")])
                if uuid_id: # if another is linked update res_id
                    mapping_obj.write(cr, uid, [uuid_id], {"res_id" : oid, "active" : True } )
                else: # create new 
                    uuid_id = mapping_obj.create(cr, uid, { "uuid" : uuid,
                                                            "res_model" : "dataset.dataset",
                                                            "res_id" : oid })
        else:
            uuid_id = mapping_obj.search_id(cr, uid, [("name","=",None),("uuid","=",uuid),("res_model","=","dataset.dataset"),("res_id","=",oid)])
            if uuid_id:
                parent_id = self.search_id(cr, uid, [("name","=",None),("uuid","=",uuid),("parent_id","=",None)])
                if parent_id: # set new parent if uuid is linked to current and parent_id is set
                    mapping_obj.write(cr, uid, uuid_id, {"res_id" : parent_id, "active" : True })
        return True
    
    def _data_copy_domain_impl(self, cr, uid, domain=None, schema=None, context=None):
        domain = domain and list(domain) or []
        domain.append(("parent_id","=",None))
        domain.append(("cfield_id","=",None))
        return domain
        
    def _data_read_obj_impl(self, cr, uid, obj, schema=None, refonly=False, context=None):
        return self._data_read(cr, uid, obj, schema=schema, refonly=refonly, context=context)
  
    def data_def_impl(self, cr, uid, schema=None, add_description=False, context=None):
        return self.pool.get("dataset.spec").data_def(cr, uid, "dataset.dataset", schema, add_description=add_description, context=context)
  
    def data_write_impl(self, cr, uid, data, schema=None, context=None):
        return self._data_write(cr, uid, data, schema=schema, context=context)
    
    def data_read_impl(self, cr, uid, uuid, schema=None, refonly=False, context=None):
        obj = self.pool.get("res.mapping")._browse_mapped(cr, uid, uuid, context=context)
        return self._data_read(cr, uid, obj, schema=schema, refonly=refonly, context=context)
    
    def create(self, cr, uid, vals, context=None):
        res = super(dataset_dataset,self).create(cr, uid, vals, context=context)
        self._update_uuid(cr, uid, res, context=context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(dataset_dataset,self).write(cr, uid, ids, vals, context=context)
        if vals.has_key("parent_id") or vals.has_key("uuid"):
            if isinstance(ids, (int, long)):
                ids = [ids]
            for oid in ids:
                self._update_uuid(cr, uid, oid, context=context)
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        #
        mapping_obj = self.pool.get("res.mapping")
        uuid_ids = mapping_obj.search(cr, uid, [("name","=",None),("res_model","=","dataset.dataset"),("res_id","in",ids)])
        mapping_obj.write(cr, uid, uuid_ids, {"active" : False}, context=context)
        #
        return super(dataset_dataset,self).unlink(cr, uid, ids, context=context)
   
    _name = "dataset.dataset"
    _description = "Dataset"
    _parent_store = True
    _order = 'parent_left'
    _columns = {        
        "uuid" : fields.char("UUID",select=True,required=True),
        "name" : fields.char("Name",select=True),
        "cfield_id" : fields.many2one("dataset.field","Composition Field", ondelete="cascade"),
        "field_ids" : fields.one2many("dataset.field","dataset_id","Fields"),
        "parent_id" : fields.many2one("dataset.dataset","Next Version",select=True,ondelete="cascade"),
        "parent_left" : fields.integer("Left Parent",select=True),
        "parent_right" : fields.integer("Right Parent",select=True),
        "version_ids" : fields.function(_version, type="many2many", obj="dataset.dataset", string="Versions", store=False),
     }
    _defaults = {
       "uuid" : lambda self,cr,uid,context: uuid.uuid4().hex
    }

    
class dataset_field(osv.Model):
    
    def _value(self,cr,uid,field):
        if field.dtype == "s":
            return field.value
        elif field.dtype == "f":
            return field.value_float
        elif field.dtype == "i":
            return field.value_int
        elif field.dtype == "t":
            return field.value_text
        elif field.dtype == "b":
            return field.value_int and True or False
        elif field.dtype == "c":
            dataset_obj =self.pool.get("dataset.dataset")
            dataset_id = dataset_obj.search_id(cr,uid,[("cfield_id","=",field.id)])
            if dataset_id:
                return dataset_obj.browse(cr,uid, dataset_id)
        elif field.dtype == "r":            
            return self.pool.get("res.mapping")._browse_mapped(cr, uid, field.value)
        elif field.dtype == "l":
            res = []
            for child in field.child_ids:
                res.append(self._value(cr,uid,child))
            return res
        return None
    
    _name = "dataset.field"
    _description = "Dataset Field"
    _columns = {        
        "name" : fields.char("Name",select=True),        
        "dataset_id" : fields.many2one("dataset.dataset","Dataset",select=True,ondelete="cascade"),
        "parent_id" : fields.many2one("dataset.field","List",select=True,ondelete="cascade"),
        "child_ids" : fields.one2many("dataset.field","parent_id","Entries"),                
        "dtype" : fields.selection([("s","String"),
                                   ("i","Integer"),
                                   ("b","Boolean"),
                                   ("f","Float"),
                                   ("t","Text"),
                                   ("r","Reference"),
                                   ("c","Composition"),
                                   ("l","List")],
                                  "Type",select=True,required=True),
        "value" : fields.char("String Value",select=True),
        "value_int" : fields.integer("Integer Value",select=True),
        "value_float" : fields.float("Float Value",select=True),
        "value_text" : fields.text("Text Value"),
        "value_id" : fields.many2one("dataset.dataset","Dataset Value", ondelete="cascade", select=True),
        "sequence" : fields.integer("Sequence")
    }
    _order = "dataset_id, parent_id, sequence"

class dataset_spec(osv.Model):

    def data_def(self, cr, uid, model, name, add_description=False, context=None):
        if not context:
            context = {}
        
        #create result
        field_defs = {}
        res =  {
            "fields" : field_defs,
            "model" : model
        }
        
        spec_id = self.search_id(cr, uid, [("name","=",name)],context=context)
        if not spec_id:
            return res
        
        spec = self.browse(cr, uid, spec_id, context)
        res["schema"]=spec.name
        res["label"]=spec.label
        res["max_versions"]=spec.max_versions

        if add_description:
            res["description"]=spec.description
        #                
        for field in spec.field_ids:
            field_name = field.name
            field_def = {
                "name" : field_name,
                "label" : field.label,
                "dtype" : field.dtype,
            }

            field_def["spec"]=spec.dtype_spec_id.name
        
            if add_description:
                res["description"]=field.description
            
            field_defs[field_name]=field_def

        return res

    _name = "dataset.spec"
    _description = "Dataset Specification"
    _columns = {                
        "name" : fields.char("Name",select=True,required=True),
        "label" : fields.char("Label",translate=True,required=True),        
        "description" : fields.text("Description",translate=True),
        "field_ids" : fields.one2many("dataset.spec.field","spec_id","Fields"),
        "max_versions" : fields.integer("Max Versions",help="Count of Versions to Keep in Database")
    }
    
    
class dataset_spec_field(osv.Model):
    _name = "dataset.spec.field"
    _description = "Dataset Specification Field"
    _columns = {
        "spec_id" : fields.many2one("dataset.spec","Dataset Specification",required=True,select=True),
        "name" : fields.char("Name",select=True,required=True),
        "label" : fields.char("Label",translate=True,required=True),
        "description" : fields.text("Description",translate=True),
        "dtype" : fields.selection([("s","String"),
                                   ("i","Integer"),
                                   ("f","Float"),
                                   ("t","Text"),
                                   ("r","Reference"),
                                   ("c","Composition"),
                                   ("l","List")],
                                  "Type",select=True),
        "dtype_spec_id" : fields.many2one("dataset.spec","Type Specification",ondelete="set null")        
    }
    
   
class dataset_view(osv.Model):
    
    def _data_def(self, cr, uid, model_obj, view=None, add_description=False, recursion_set=None, context=None):
        if not context:
            context = {}
                       
        #check recursion
        if recursion_set and model_obj._name in recursion_set:
            raise DataDefRecursion
                       
        #create result
        field_defs = {}
        res =  {
            "fields" : field_defs,
            "model" : model_obj._name            
        }
       
        field_alias={}
        field_views={}
        field_include=set()
        field_exclude=set()
        field_ltype={}
        field_hidden={}
        
        if not view:
            view = self._schema_get(cr, uid, model_obj._name, context)
        
        if view:
            res["schema"]=view.name
            if view.ltype:
                res["ltype"]=view.ltype
            
            for rule in view.rule_ids:
                rule_field = rule.field_id
                if not rule_field:
                    continue
                # options
                if rule.option=="i":
                    field_include.add(rule_field.name)
                elif rule.option=="e":
                    field_exclude.add(rule_field.name)
                elif rule.option=="h":
                    field_hidden[rule_field.name]=True
                elif rule.option=="v":
                    field_hidden[rule_field.name]=False
                # view
                rule_view = rule.field_view_id             
                if rule_view:     
                    field_views[rule_field.name]=rule_view.name
                    # flags
                    if rule_view.ltype:
                        field_ltype[rule_field.name]=rule_view.ltype
                        
                # alias
                field_alias[rule_field.name]=rule.name
                # flags
                if rule.ltype:
                    field_ltype[rule_field.name]=rule.ltype                     
        
        fields = model_obj.fields_get(cr, uid)
        for field, attrib in fields.items():
            # exclude field
            if field in field_exclude:
                continue
            # exclude not included field if included fields are defined
            if field_include and not field in field_include:
                continue
       
            field_type = attrib.get("type")
            field_relation = attrib.get("relation") or None
            field_name = field_alias.get(field) or field            
            field_view = field_views.get(field_name)
            field_def = {}
            
            # default hide function fields
            field_function = attrib.get("function") or None
            if field_function:
                field_def["hidden"]=True
                
            # get sub list or composite type
            sub_view_name = field_view or field_relation
            sub_view = None
            if sub_view_name:
                sub_view = self._schema_get(cr, uid, sub_view_name, context)
                if sub_view and sub_view.ltype:
                    sub_ltype_hint = sub_view.ltype 
            #
            sub_ltype_hint = field_ltype.get(field)
            sub_ltype = sub_ltype_hint or "r"
                
            # evaluate type
            if field_type == "many2one":
                field_def["dtype"]=sub_ltype
                if field_relation and not field_function:
                    rel_fields = fields
                    if not field_relation == model_obj._name:
                        rel_fields = self.pool.get(field_relation).fields_get(cr, uid)
                    for rel_attrib in rel_fields.values():
                        if rel_attrib.get("relation") == model_obj._name and rel_attrib.get("relation_field") == field:
                            field_def["hidden"]=True
            elif field_type == "one2many":
                if not sub_ltype_hint and field_relation != model_obj._name:
                    #check recursion
                    if recursion_set is None:
                        recursion_set = set()
                    recursion_set.add(model_obj._name)
                    try:
                        sub_ltype="c"
                        #check recursion
                        self._data_def(cr, uid, self.pool.get(field_relation), 
                                                view=sub_view, 
                                                add_description=False, 
                                                recursion_set=recursion_set, context=context )
                        
                        #check for parent relation
                        rel_fields = self.pool.get(field_relation).fields_get(cr, uid)
                        for rel_attrib in rel_fields.values():
                            if rel_attrib.get("type") == "one2many" and not rel_attrib.get("function") and rel_attrib.get("relation") == field_relation:
                                sub_ltype="r"
                                break
                         
                    except DataDefRecursion:
                        sub_ltype="r"
                    finally:
                        recursion_set.remove(model_obj._name)

                field_def["dtype"]="l"
                field_def["ltype"]=sub_ltype
                field_def["hidden"]=(sub_ltype=="r")
            elif field_type == "many2many":
                field_def["dtype"]="l"
                field_def["ltype"]=field_ltype.get(field,"r")
            elif field_type == "char":
                field_def["dtype"]="s"
            elif field_type == "integer":
                field_def["dtype"]="i"
            elif field_type == "float":
                field_def["dtype"]="f"
            elif field_type == "text":
                field_def["dtype"]="t"
            else:
                continue
            
            # hidden override
            if field_hidden.has_key(field):
                field_def["hidden"]=field_hidden[field]
            
          
            field_label  = attrib.get("string")
            field_def["name"]=field
            field_def["label"]=field_label
                              
            if add_description:
                field_def["description"]=attrib.get("help")
            if field_relation:
                field_def["model"]=field_relation
            if field_view:
                field_def["schema"]=field_view
                               
            field_defs[field_name]=field_def
        
        return res
    
    def _data_read(self, cr, uid, model_obj, obj, schema=None, refonly=False, context=None):
        res = {}
        
        definition = self.data_def(cr, uid, model_obj._name, schema=schema, context=context)
        model = definition["model"]
        res[META_MODEL]=model
        
        schema=definition.get("schema")
        if schema and schema != model:
            res[META_SCHEMA]=schema
        
        mapping_obj = self.pool.get("res.mapping")       
        res[META_ID]=mapping_obj.get_uuid(cr, uid, model_obj._name, obj.id)
        
        if refonly:
            return res
        
        fields = definition["fields"]
        for name, attrib in fields.items():
            # check for hidden attribute
            if attrib.get("hidden"):
                continue
            # get type
            dtype = attrib["dtype"]
            # reset value
            value = None
            
            # evaluate composite, reference and list type
            if dtype in ("c","r","l"):
                # get model and view
                dtype_model = attrib["model"]
                dtype_model_schema = attrib.get("schema")
                # uuid helper function
                def get_value(dtype_obj,refonly):
                    if not dtype_obj:
                        return None
                    uuid = mapping_obj.get_uuid(cr, uid, dtype_model, dtype_obj.id)
                    return uuid and self.data_read(cr, uid, dtype_model, uuid, schema=dtype_model_schema, refonly=refonly, context=context) or None
                # prepare single type
                if dtype in ("c","r"):
                    dtype_obj = getattr(obj, attrib["name"])
                    value = get_value(dtype_obj,refonly=(dtype=="r"))
                else:
                    dtype_objs = getattr(obj, attrib["name"])
                    value = []
                    for dtype_obj in dtype_objs:
                        list_value = get_value(dtype_obj,refonly=(attrib.get("ltype")=="r"))
                        if list_value:
                            value.append(list_value)
            
            # evaluate primitive values
            else:
                value = getattr(obj, attrib["name"])
                
            res[name]=value
            
        return res
    
    def _parse_field(self, cr, uid, name, data, field_def, schema=None, context=None):
        res = None
        if data:
            dtype = field_def["dtype"]
            if dtype == "c":
                ref = self.data_write(cr, uid, data, field_def["model"], schema=field_def.get("schema"), context=context)
                res = self.pool.get("res.mapping").get_id(cr, uid, ref[META_MODEL], ref[META_ID])
                if not res:
                    raise osv.except_osv(_("Error!"), _("Unable to link field %s with data %s"), (field_def["name"], data))
            elif dtype == "r":
                res = self.pool.get("res.mapping").get_id(cr, uid, data.get(META_MODEL) or field_def["model"], data[META_ID])
                if not res:
                    raise osv.except_osv(_("Error!"), _("Unable to find reference with UUID %s") % (data[META_ID],))
            elif dtype == "l":
                res = []
                for list_data in data:
                    if list_data:
                        list_field_def = field_def.copy()
                        list_field_def["dtype"] = is_ref(data) and "r" or "c"
                        res.append(self._data_write_field(cr, uid, name, data, list_field_def, schema=schema, context=context))
                res = [(6,0,res)]
            else:
                res = data                    
        return res
        
    def _data_write(self, cr, uid, model_obj, data, schema=None, context=None):
        # get data definition
        fields = self.data_def(cr, uid, model_obj._name, schema=schema, context=context)["fields"]
        
        # get id
        mapping_obj = self.pool.get("res.mapping")       
        uuid = data.get(META_ID)
        oid = None
        if uuid:
            oid=mapping_obj.get_id(cr, uid, model_obj._name, uuid)
        
        # values to write
        values = {}
        #
        for name, field_def in fields.items():
            if not data.has_key(name):
                continue
            #
            field_data = data[name]
            value = self._parse_field(cr, uid, name, field_data, field_def, schema=schema, context=context)
            values[name]=value  
          
        
        # check if values are found
        if not values:
            raise osv.except_osv(_("Error!"), _("Cannot write %s into model %s") % (data,model_obj._name))
        
        if oid: #write
            model_obj.write(cr, uid, [oid], values, context=context)
        else:   #create
            oid = model_obj.create(cr, uid, values, context=context)
        
        # build result
        obj = model_obj.browse(cr, uid, oid, context=context)
        return self._data_read(cr, uid, model_obj, obj, schema=schema, refonly=True, context=context)
    
    def _schema_get(self, cr, uid, name, context=None):
        if name:
            view_id = self.search_id(cr, uid, [("name","=",name)])
            return view_id and self.browse(cr, uid, view_id, context=context) or None
        return None    
         
    def _data_last_change(self, cr, uid, model_obj, domain=None, context=None):
        # determine last changed id
        res = None
        last_changed_id = model_obj.search_id(cr, uid, domain, order="write_date desc", context=context)
        if last_changed_id:
            query = "SELECT write_date FROM %s WHERE id = %s" % (model_obj._table,last_changed_id)
            cr.execute(query)
            row = cr.fetchone()
            res = row and row[0]
        return res
       
    def _data_last_delete(self, cr, uid, model_obj, context=None):
        field_active = self.fields_get(cr, uid, ["active"], context=context)
        
        context = context and context.copy() or {}
        context["active_test"]=False
        domain = [("active","=",False)]
        #
        model_change = None
        if field_active:
            model_change = self._data_last_change(cr, uid, model_obj, domain=domain, context=context)
        #
        mapping_obj = self.pool.get("res.mapping")        
        uuid_change = self._data_last_change(cr, uid, mapping_obj, domain=domain, context=context)
        #
        return max(model_change,uuid_change)
    
    def _data_changed_ids(self, cr, uid, model_obj, domain=None, schema=None, chgmark=None, context=None):
        domain = self._data_copy_domain(cr, uid, model_obj, domain, schema, context)
        # add sync point
        if chgmark:
            domain.append(("write_date",">",chgmark))
        return model_obj.search(cr, uid, domain, context=context)
    
    def _data_validate_mapping(self, cr, uid, model_obj, context=None):
        # update mapping
        cr.execute("SELECT m.id FROM res_mapping m "
                   " LEFT JOIN %s t ON t.id = m.res_id " 
                   "WHERE m.res_model = '%s' AND m.active = 't' AND t.id IS NULL " % (model_obj._table, model_obj._name))
        ids = [row[0] for row in cr.fetchall()]
        mapping_obj = self.pool.get("res.mapping")
        mapping_obj.write(cr, uid, ids, {"active":False}, context=context)
    
    def _data_deleted_uuids(self, cr, uid, model_obj, delmark=None, context=None):
        domain = [("name","=",False),("res_model","=",model_obj._name),("active","=",False)]
        if delmark:
            domain.append(("write_date",">",delmark))

        mapping_obj = self.pool.get("res.mapping")  
        ids = mapping_obj.search(cr, uid, domain, context=context)
        return ids and [r["uuid"] for r in mapping_obj.read(cr,uid,ids,["uuid"],context=context)] or []
    
    def _data_changeset(self, cr, uid, model_obj, domain=None, schema=None, context=None):
        res = {
            "model" : model_obj._name  
        }
        if domain:
            res["domain"]=domain # original domain
        if schema:
            res["schema"]=schema
                  
        # copy domain and add additional fix base queries, rules
        domain = self._data_copy_domain(cr, uid, model_obj, domain, schema, context)
              
        mark = self._data_last_change(cr, uid, model_obj, domain=domain, context=context)
        if mark:
            res["chgmark"]=mark
            
        mark = self._data_last_delete(cr, uid, model_obj, context=context)
        if mark:
            res["delmark"]=mark
        return res
    
    def _data_read_obj(self, cr, uid, model_obj, obj, schema=None, refonly=False, context=None):
        f = get_method(model_obj, "_data_read_obj_impl")
        if f:
            return f(cr, uid, obj, schema=schema, refonly=refonly, context=context)
        
        schema = self._schema_get(cr, uid, schema, context=context)
        return self._data_read(cr, uid, model_obj, obj, schema=schema, refonly=refonly, context=context)
    
    def _data_copy_domain(self, cr, uid, model_obj, domain=None, schema=None, context=None):
        f = get_method(model_obj, "_data_copy_domain_impl")
        if f:
            return f(cr, uid, domain=domain, schema=schema, context=context)
        return domain and list(domain) or []
    
    def _model_field_ids(self, cr, uid, model_id):
        ir_model_obj = self.pool.get("ir.model")
        model = ir_model_obj.browse(cr, uid, model_id)
        fields = OrderedDict()
        if model:
            model_obj = self.pool.get(model.model)
            if model_obj:
                ir_field_obj = self.pool.get("ir.model.fields")
                for inherited in model_obj._inherits:
                    inherited_id = ir_model_obj.search_id(cr,uid,[("model","=",inherited)])
                    if inherited_id:
                        inh_fields = ir_model_obj.read(cr,uid,inherited_id,["field_id"])["field_id"]
                        for field in ir_field_obj.browse(cr,uid,inh_fields):
                            fields[field.name]=field.id
                            
            for field in model.field_id:
                fields[field.name]=field.id
        return list(fields.values())
    
    def _available_fields_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for view in self.browse(cr, uid, ids, context):
            model = view.model_id
            if model:
                res[view.id]=self._model_field_ids(cr, uid, view.model_id.id)
        return res
    
    @ormcache()
    def _data_def_cached(self, cr, uid, model, schema, lang, add_description):
        context = {}
        if lang:
            context["lang"]=lang
        model_obj = self.pool.get(model)
        if not model_obj:
            raise osv.except_osv(_("Error!"), _("Invalid Model %s") % (model,))
        
        f = get_method(model_obj,"data_def_impl")
        if f:
            return f(cr, uid, schema=schema, add_description=add_description, context=context)
        
        schema = self._schema_get(cr, uid, schema, context)        
        return self._data_def(cr, uid, model_obj, view=schema, context=context)
    
    def _chgnotify(self, cr, uid, context=None):
        self.clear_caches()
        super(dataset_view,self)._chgnotify(cr, uid, context=context)
        
    def on_change_model(self, cr, uid, ids, model_id, context=None):
        res = { "value" : { "model_field_ids" : [] }}
        if model_id:
            res["value"]["model_field_ids"]=self._model_field_ids(cr, uid, model_id)
        return res
         
    def data_changeset(self, cr, uid, model, domain=None, schema=None, context=None):
        model_obj = self.pool.get(model)
        if not model_obj:
            raise osv.except_osv(_("Error!"), _("Invalid Model %s") % (model,))        
        return self._data_changeset(cr, uid, model_obj, domain=domain, schema=schema, context=context)
    
    def data_exchange(self, cr, uid, changes, models=None, params=None, context=None):
        client_changes = changes or []
        server_changes = []
        uuid_set = set()
        
        for model in models:
            model_param = params and params.get(model) or None
            
            domain = None
            schema = None
            chgmark = None
            delmark = None
            
            if model_param:
                domain = model_param.get("domain")
                schema = model_param.get("schema")
                chgmark = model_param.get("chgmark")
                delmark = model_param.get("delmark")
            
            # check model
            model_obj = self.pool.get(model)
            if not model_obj: 
                raise osv.except_osv(_("Error!"), _("Model %s is unknown") % (model,))
            
            # prepare server changes
            changed_ids = self._data_changed_ids(cr, uid, model_obj, domain=domain, schema=schema, chgmark=chgmark, context=context) 
            server_changes = []
            for obj in model_obj.browse(cr, uid, changed_ids, context=context):
                data = self._data_read_obj(cr, uid, model_obj, obj, schema=schema, context=context)
                uuid_set.add(data[META_ID])
                server_changes.append(data)
                
            # prepare server deletes
            if delmark:
                for uuid in self._data_deleted_uuids(cr, uid, model_obj, delmark, context):
                    server_changes.append( { META_ID : uuid, 
                                             META_DELETE : True } )
                    uuid_set.add(uuid)
        
        #process client change
        for change in client_changes:
            if change.get(META_DELETE):
                self.data_unlink(cr, uid, model, change, context)
            else:
                change_uuid = change[META_ID]
                model = change.get(META_MODEL) or "dataset.dataset"
                #
                model_param = params and params.get(model) or None
                schema = change.get(META_SCHEMA) or (model_param and model_param.get("schema") or None)
                #
                if not change_uuid in uuid_set:
                    self.data_write(cr, uid, change, model, schema=schema, context=context)
            
        #create result
        result = dict.fromkeys(models)
        for model in models:
            model_param = params and params.get(model) or None
            domain = model_param and model_param.get("domain") or None
            schema = model_param and model_param.get("schema") or None
            model_chg = self.data_changeset(cr, uid, model, domain=domain, schema=schema, context=context)
            model_chg.pop("model") # remove model 
            result[model] = model_chg
        
        return {
            "result" : result,
            "changes" : server_changes
        }
    
    def data_sync(self, cr, uid, changeset, context=None):   
        domain = changeset.get("domain") 
        model = changeset.get("model")
        schema = changeset.get("schema")
        chgmark = changeset.get("chgmark")
        delmark = changeset.get("delmark")
        client_changes = changeset.get("chgs")
        client_deletes = changeset.get("dels")
         
        if not model:
            raise osv.except_osv(_("Error!"), _("Model is empty"))
         
        #if model.startswith("res."):
        #    raise osv.except_osv(_("Error!"), _("Resource Model %s are not allowed") % (model,))
                 
        model_obj = self.pool.get(model)
        if not model_obj: 
            raise osv.except_osv(_("Error!"), _("Model %s is unknown") % (model,))
         
        uuid_set = set()
        # validate uuid mapping
        self._data_validate_mapping(cr, uid, model_obj, context)
         
        # build server changes
        changed_ids = self._data_changed_ids(cr, uid, model_obj, domain=domain, schema=schema, chgmark=chgmark, context=context) 
        server_changes = []
        for obj in model_obj.browse(cr, uid, changed_ids, context=context):
            data = self._data_read_obj(cr, uid, model_obj, obj, schema=schema, context=context)
            uuid_set.add(data[META_ID])
            server_changes.append(data)
         
        # non conflicting changes
        if client_changes:
            valid_changes = []
            for change in client_changes:
                res_uuid = change[META_ID]
                if not res_uuid in uuid_set:
                    valid_changes.append(change)
                 
            # process client changes
            if valid_changes:            
                for change in valid_changes:
                    self.data_write(cr, uid, change, model, schema=schema, context=context)
                 
        # get deletions
        server_deletes=None
        if delmark:
            server_deletes = self._data_deleted_uuids(cr, uid, model_obj, delmark, context)
            uuid_set.update(server_deletes)
        else:
            server_deletes=[]
         
        # prepare, check deletes
        if client_deletes:
            # delete only wich are not changed by server
            client_deletes = list(set(client_deletes).difference(uuid_set))
            # unlink uuid
            mapping_obj = self.pool.get("res.mapping")
            mapping_obj.unlink_uuid(cr, uid, client_deletes, context=context)
 
        # build result
        res = self.data_changeset(cr, uid, model, domain, schema, context)
        res["chgs"]=server_changes
        res["dels"]=server_deletes
        return res
    
    def data_def(self, cr, uid, model, schema=None, add_description=False, context=None):
        return self._data_def_cached(cr, uid, model, schema, (context and context.get("lang") or None), add_description)
   
    def data_unlink(self, cr, uid, model, uuid, context=None):
        if not uuid:
            raise osv.except_osv(_("Error!"), _("UUID is empty"))
        
        mapping_obj = self.pool.get("res.mapping")
        return mapping_obj.unlink_uuid(cr, uid, uuid, context=context)
   
    def data_read(self, cr, uid, model, uuid, schema=None, refonly=False, context=None):
        if not uuid:
            raise osv.except_osv(_("Error!"), _("UUID is empty"))
        model_obj = self.pool.get(model)
        if not model_obj:
            raise osv.except_osv(_("Error!"), _("Invalid Model %s") % (model,))

        f = get_method(model_obj, "data_read_impl")
        if f:
            return f(cr, uid, uuid, schema=schema, refonly=refonly, context=context)
        
        # get mapped object via uuid
        mapping_obj = self.pool.get("res.mapping")        
        obj = mapping_obj._browse_mapped(cr, uid, uuid, context=context)
        return self._data_read(cr, uid, model_obj, obj, schema=schema, refonly=refonly, context=context)
        
    def data_write(self, cr, uid, data, model=None, schema=None, context=None):
        # no write without data
        if not data:
            raise osv.except_osv(_("Error!"), _("No Data"))
        # get model
        if not model:
            model=data.get(META_MODEL)
        model_obj = self.pool.get(model)
        if not model_obj:
            raise osv.except_osv(_("Error!"), _("Invalid Model"))
        # get schema
        if not schema:
            schema=data.get(META_SCHEMA)
        # check for other data write impl
        f = get_method(model_obj,"data_write_impl")
        if f: 
            return f(cr, uid, data, schema=schema, context=context)
        schema = self._schema_get(cr, uid, schema, context)
        return self._data_write(cr, uid, model_obj, data, schema=schema, context=context)
    
    def data_last_change(self, cr, uid, model, schema=None, domain=None, context=None):
        model_obj = self.pool.get(model)
        if not model_obj:
            raise osv.except_osv(_("Error!"), _("Invalid Model"))
        f = get_method(model_obj, "data_last_change_impl")
        if f:
            return f(cr, uid, schema=schema, domain=domain, context=context)
        view = self._schema_get(cr, uid, schema, context)
        return self._data_last_change(cr, uid, model_obj, view=view, domain=domain, context=context)

    _name = "dataset.view"
    _description = "Dataset View"
    _columns = {
        "name" : fields.char("Name",select=True),
        "model_id" : fields.many2one("ir.model","Model",select=True,ondelete="set null"),
        "model_field_ids" : fields.function(_available_fields_ids,type="many2many",relation="ir.model.fields",string="Model Fields"),
        "rule_ids" : fields.one2many("dataset.view.rule","view_id",string="Rules"),
        "ltype" : fields.selection([("c","Composition"),("r","Reference")],"Link Type",select=True)   
    }

    
class dataset_view_rule(osv.Model):
    
    def on_change_field(self, cr, uid, ids, field_id):               
        res = { "value" : { "field_relation" : None }}
        if field_id:
            field = self.pool.get("ir.model.fields").browse(cr,uid,field_id)
            res["value"]["field_relation"] = field.relation            
        return res
    
    _name = "dataset.view.rule"
    _description = "Dataset Rule"
    _columns = {
        "view_id" : fields.many2one("dataset.view","View",select=True,ondelete="cascade"),
        "name" : fields.char("Alias",select=True),        
        "field_id" : fields.many2one("ir.model.fields","Field",select=True,ondelete="set null"),
        "field_view_id" : fields.many2one("dataset.view","Field View",ondelete="set null"),
        "field_relation" : fields.related("field_id","relation",relation="ir.model.fields",type="char",size=64,string="Field Relation"),
        "option" : fields.selection([("i","Include"),("e","Exclude"),("h","Hidden"),("v","Visible")],"Option",select=True),
        "ltype" : fields.selection([("c","Composition"),("r","Reference")],"Link Type",select=True),
        "sequence" : fields.integer("Sequence")
    }
    _order = "view_id, sequence asc"