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
from openerp.addons.at_base import util
from openerp.addons.at_base import helper
from openerp.exceptions import AccessError
from openerp.tools.translate import _

import simplejson
import openerp
import uuid
import couchdb
import hashlib

import re

PATTERN_REV = re.compile("^([0-9]+)-(.*)$")

META_ID = "_id"
META_REV = "_rev"
META_DELETE = "_deleted"
META_NAME = "_name"
META_MODEL  = "fdoo__ir_model"

META_FIELDS = set([
 META_ID,
 META_MODEL,
 META_DELETE,
 META_NAME,
 META_REV 
])

from openerp import SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)

# Helper

def isMetaField(name):
    """ :return: True if it is a meta data field """
    return name.startswith("_") or name in META_FIELDS

def isReference(vals):
    if vals and vals.get(META_ID):
        for field in vals.keys():
            if not isMetaField(field):
                return False
        return True
    return False

def getAttrOrNone(model_obj, name):
    try:
        return getattr(model_obj, name)
    except AttributeError:
        return None

class DefRecursionException(Exception):
    """ Recursion Exception """
    pass


class jdoc_jdoc(osv.AbstractModel):
    
    def _jdoc_create_def(self, cr, uid, model_obj, recursion_set=None, context=None):
        """
        Create jdoc Definition from Model
        
        Field Attribute(s): 
            
            composition 
            export
                        
            
        Class Attribute(s):
        
            _composition
        
        """
        if not context:
            context = {}
            
                               
        #check recursion
        if recursion_set and model_obj._name in recursion_set:
            raise DefRecursionException
        
        #create result
        field_defs = {}
        res =  {
            "fields" : field_defs,
            "model" : model_obj._name            
        }
        
        # get fields
        def getFields(model_obj, m):
            for parent in model_obj._inherits:
                getFields(self.pool[parent], m=m)
            for name, field in model_obj._columns.iteritems():
                m[name]=field
            return m
        
        def isComputed(field_obj):
            return isinstance(field_obj, fields.function)
            
        all_fields = getFields(model_obj, {})
        for field, field_obj in all_fields.iteritems():
            if field == "id":
                continue
                 
            field_type = field_obj._type
            if field_type == "selection":
                field_type = "char"
                if field_obj.selection:
                    
                    selection = field_obj.selection
                    if hasattr(selection, '__call__'):
                        #selection = field_obj.selection()
                        selection = None
                        
                    if selection:
                        for sel in selection:
                            sel_value = sel[0]
                            if not sel_value:
                                continue
                            if isinstance(sel_value, basestring):
                                field_type = "char"
                                break
                            if isinstance(sel_value,(int,long)):
                                field_type = "integer"
                                break
                            elif isinstance(sel_value,float):
                                field_type = "float"
                                break
                            
            
            field_relation = field_obj._obj
            field_name = getAttrOrNone(field_obj,"alias") or field          
            field_def = {}
            
            # default hide function fields
            is_computed = isComputed(field_obj)
            if is_computed:
                field_def["hidden"]=True
            
            sub_ltype_hint = None
            
            # get sub ltype    
            if field_relation:
                sub_model_obj = self.pool[field_relation]
                composition = getAttrOrNone(sub_model_obj,'_composition') 
                if composition is True:
                    sub_ltype_hint = "c"
                if composition is False:
                    sub_ltype_hint = "r"
                 

            # determine sub list type
            composition = getAttrOrNone(field_obj,"composition")
            if composition is True:
                sub_ltype_hint = "c"
            if composition is False:
                sub_ltype_hint = "r"
                
            sub_ltype = sub_ltype_hint or "r"

            # evaluate type
            if field_type == "many2one":
                field_def["dtype"]=sub_ltype
# DISABLED auto DETECTION                
#                 if field_relation and not is_computed:
#                     rel_fields = all_fields
#                     if not field_relation == model_obj._name:
#                         rel_fields = getFields(self.pool.get(field_relation), {})
#                     for rel_field in rel_fields.itervalues():
#                         if rel_field._obj == model_obj._name and rel_field._type == "one2many":
#                             if rel_field._fields_id == field:
#                                 field_def["hidden"]=True
            elif field_type == "one2many":
# DISABLED auto DETECTION
#                 if not sub_ltype_hint and field_relation != model_obj._name:
#                     #check recursion
#                     if recursion_set is None:
#                         recursion_set = set()
#                     recursion_set.add(model_obj._name)
#                     try:
#                         sub_ltype="c"
#                         
#                         #check recursion
#                         sub_model_obj = self.pool.get(field_relation)                        
#                         self._jdoc_create_def(cr, uid, sub_model_obj,
#                                                         recursion_set=recursion_set, 
#                                                         context=context)
#                         
#                         #check for parent relation
#                         rel_fields = getFields(self.pool.get(field_relation))
#                         for rel_field in rel_fields.values():
#                             if rel_field._type == "one2many" and not isComputed(rel_field) and rel_field._obj == field_relation:
#                                 sub_ltype="r"
#                                 break
#                          
#                     except DefRecursionException:
#                         sub_ltype="r"
#                     finally:
#                         recursion_set.remove(model_obj._name)
                
                field_def["one2many"]=field_obj._fields_id
                field_def["dtype"]="l"
                field_def["ltype"]=sub_ltype
                field_def["hidden"]=(sub_ltype=="r")
            elif field_type == "many2many":
                field_def["dtype"]="l"
                field_def["ltype"]=getAttrOrNone(field_obj,"composition") or "r"
            elif field_type == "char":
                field_def["dtype"]="s"
            elif field_type == "integer":
                field_def["dtype"]="i"
            elif field_type == "float":
                field_def["dtype"]="f"
            elif field_type == "text":
                field_def["dtype"]="t"
            elif field_type == "boolean":
                field_def["dtype"]="b"
            elif field_type == "date":
                field_def["dtype"]="d"
            elif field_type == "datetime":
                field_def["dtype"]="dt"
            else:
                continue
            
            # check if field is not visible
            field_invisible = getAttrOrNone(field_obj,"invisible")
            if field_invisible:
                field_def["hidden"]=True
            else:            
                # if export is explicit set
                # correct hidden
                # field could not hidden
                field_export = getAttrOrNone(field_obj,"export")
                if field_export:
                    field_def["hidden"]=False
                elif field_export is False:
                    field_def["hidden"]=True
          
            field_def["name"]=field
            if field_relation:
                field_def["model"]=field_relation
            field_defs[field_name]=field_def        
        return res
    
    def _jdoc_access(self, cr, uid, res_model, res_id, auto=False, context=None):
        # update access
        curUTC = util.currentUTCDateTime()
        if auto:
            cr.execute("UPDATE jdoc_usage SET used=%s, auto=%s WHERE res_model=%s AND res_id=%s AND user_id=%s", (curUTC, True, res_model, res_id, uid))
        else:
            cr.execute("UPDATE jdoc_usage SET used=%s WHERE res_model=%s AND res_id=%s AND user_id=%s", (curUTC, res_model, res_id, uid))
        if not cr.rowcount:
            usage_obj = self.pool.get("jdoc.usage")
            usage_obj.create(cr, uid, {
                "used" : util.currentDateTime(),
                "user_id" : uid,
                "res_model" : res_model,
                "res_id" : res_id,
                "auto" : auto
            }, context=context)
       
    def _jdoc_get(self, cr, uid, obj, refonly=False, options=None, context=None):
        if not obj:
            return False
        
        if not options:
            options = {}
        
        mapping_obj = self.pool.get("res.mapping")       
        doc_uuid = mapping_obj.get_uuid(cr, uid, obj._name, obj.id)
        if refonly:
            return doc_uuid
      
        definition = self._jdoc_def(cr, uid, obj._name)
        model = definition["model"]        
        
        res = {META_ID : doc_uuid,
               META_MODEL : model}
        
        emptyValues = True
        onlyFields = None
        compositions = None
        
        # check options
        if options:
            emptyValues = options.get("empty_values", emptyValues)
            model_options = options.get("model")
            if model_options:
                model_options = model_options.get(model)
                if model_options:
                    onlyFields = model_options.get("fields", onlyFields)
                    compositions = model_options.get("compositions", compositions)
        
        fields = definition["fields"]
        for name, attrib in fields.items():
            # check for hidden attribute, or not in fields
            if attrib.get("hidden") or (onlyFields and not name in onlyFields):
                continue
            
            # get type
            dtype = attrib["dtype"]
            # reset value
            value = None
                  
            # evaluate composite, reference and list type
            if dtype in ("c","r","l"):
                # get model
                if dtype in ("c","r"):
                    # check compositions
                    if dtype == "r" and compositions and name in compositions:
                        dtype = "c"
                    dtype_obj = getattr(obj, attrib["name"])
                    if dtype_obj:                        
                        value = self._jdoc_get(cr, uid, dtype_obj, refonly=(dtype=="r"), options=options, context=context)                    
                # handle list type 
                else:
                    dtype_objs = getattr(obj, attrib["name"])
                    ltype = attrib.get("ltype")
                    # check compositions
                    if ltype == "r" and compositions and name in compositions:
                        ltype = "c"
                    for dtype_obj in dtype_objs:
                        list_value = self._jdoc_get(cr, uid, dtype_obj, refonly=(ltype=="r"), options=options, context=context)
                        if list_value:
                            if value is None:
                                value = []
                            value.append(list_value)
            
            # evaluate primitive values
            else:
                value = getattr(obj, attrib["name"])
               
            if emptyValues or value:
                res[name]=value    
                
        #res["write_date"]=obj.write_date    
        return res
    
    def _get_uuid(self, data):
        res = hashlib.md5()
        res.update(simplejson.dumps(data))
        return res.hexdigest()
    
    def jdoc_sync(self, cr, uid, data, usage_map=None, context=None):
        """
        jdoc_sync
        @param changes: changeset to sync 
                          { "model" : xyz
                            "view" : "_jdoc_get_fclipboard",
                            lastsync: {
                                "date" : "2014-01-01 00:00:01",   # date  
                                "id"  :  3                        # highest database id from last sync from change target (odoo),
                                "seq" :  1                        # highest sequence from change source for the last sync
                                "lastchange" : {
                                    model.xy : "2014-01-01 00:00:01"
                                }
                                
                            },
                            "changes" : [
                               {
                                  "id": "doc2",
                                  "changes": [ { "rev": "2-9b50a4b63008378e8d0718a9ad05c7af" } ],
                                  "doc": {
                                    "_id": "doc2",
                                    "_rev": "2-9b50a4b63008378e8d0718a9ad05c7af",
                                    "_deleted": true
                                  },
                                  "deleted": true,
                                  "seq": 3
                               }
                            ]
                            "actions" : [
                               {
                                   "field_id" : root_id,
                                   "model": "fclipboard.item",
                                   "domain" : [['state','!=','release']],
                                   "action" : action_release                               
                               }
                           ]
        
        """
        
        # get model
        model = data["model"]  
        model_obj = self.pool[model]
        
        # get mapping
        mapping_obj = self.pool["res.mapping"]
        
        # get changes
        in_list = data.get("changes")        
        res_doc = data.get("result_format") == "doc"
                
        # get search domain
        filter_domain = data.get("domain") or []
        search_domain = list(filter_domain)
        
        # get negative/non/delete domain
        filter_ndomain = data.get("ndomain") or []
        search_ndomain = list(filter_ndomain)
        
        # check auto 
        auto = usage_map and model in usage_map
        auto_date = None
        
        # get options        
        fields = data.get("fields")
        compositions = data.get("compositions")
        options = {"empty_values" : False }
        model_options = {}
        
        if fields:
            model_options["fields"] = fields
        if compositions:
            model_options["compositions"] = compositions
        
        if model_options:
            options["model"] = {
                model : model_options
            }
            
        # get view
        view = None
        view_name = data.get("view")
        if view_name:
            view = getattr(model_obj,view_name)(cr, uid, context=context)
  
        # accelerate and use set 
        # instead of lists after
        # create domain_uuid
        if fields:
            model_options["fields"] = set(fields)
        if compositions:
            model_options["compositions"] = set(compositions)
        
        # get last sync attribs        
        lastsync = data.get("lastsync")
        
        # init last sync default
        last_date = None
        seq = 0
        first_sync = True
        lastsync_lastchange = None
        
        if lastsync:        
            last_date = lastsync.get("date", None)
            seq = lastsync.get("seq", 0)
            first_sync = (seq == 0)
            # check for resync
            if not data.get("resync"):
                lastsync_lastchange = lastsync.get("lastchange", None)
              
        # create last change if not exist
        if lastsync_lastchange is None:
            lastsync_lastchange = {}
        
        # get actions
        actions = data.get("actions")
                          
        # Method GET
        method_get = view and view.get("get") or self._jdoc_get
        # Method PUT
        method_put = view and view.get("put") or self.jdoc_put
        # Method CHANGE
        method_lastchange = view and view.get("lastchange") or None

        # process input list    
        errors = []    
        if in_list:
            changed_models = {}
            changeset = {}
            resolved_uuid2id = {}
            
            # build changeset
            for change in in_list:
                doc = change["doc"]
                doc_uuid = doc[META_ID]
                if not doc.get(META_DELETE):
                    changeset[doc_uuid] = change
            
            def put_change(change, uuid2id_resolver=None):
                doc = change["doc"]               
                return method_put(cr, uid, doc, return_id=True, uuid2id_resolver=uuid2id_resolver, changed_models=changed_models, errors=errors, usage_map=usage_map, context=context)
            
            def get_dependency(uuid):
                # check if dependency was already processed
                res = resolved_uuid2id.get(uuid, False)
                if res or res is None:
                    return res
                
                # resolve
                res = None
                change = changeset.get(uuid)
                
                if change:
                    res = put_change(change)
                    
                resolved_uuid2id[uuid] = res
                return res
                
            
            # process changes
            for change in in_list:
                doc = change["doc"]
                doc_uuid = doc[META_ID]
                seq = max(change["seq"], seq)
                 
                # check if change was already put, resolved
                if doc_uuid in resolved_uuid2id:
                    resolved_change = changeset.get(doc_uuid)
                    if resolved_change and resolved_change["seq"] == change["seq"]:
                        continue
                
                put_change(change,uuid2id_resolver=get_dependency)

                
            if actions:
                for action in actions:
                    action_model = action.get("model")
                    if not action_model:
                        continue
                    
                    method = action.get("action")
                    if not method or method.startswith("_"):
                        continue
                    
                    action_obj = self.pool[action_model]
                    if not action_obj:
                        continue
                    
                    action_ids = changed_models.get(action_model)
                    if not action_ids:
                        continue
                    
                    # determine changed ids
                    action_ids = list(action_ids)
                    field_id = action.get("field_id")
                    if field_id:
                        if field_id.startswith("_"):
                            continue
                        
                        new_action_ids = set()
                        
                        for vals in action_obj.read(cr, uid, action_ids, [field_id], context=context):
                            new_changed_id = vals[field_id]
                            
                            if isinstance(new_changed_id,tuple) and len(new_changed_id) > 0:
                                new_changed_id = new_changed_id[0]
                                
                            if new_changed_id:
                                new_action_ids.add(new_changed_id)
                            
                        action_ids = list(new_action_ids)    
                    
                    if not action_ids:
                        continue
                    
                    # check domain
                    action_domain = action.get("domain")
                    if action_domain:
                        action_domain.insert(0,("id","in",action_ids))
                        action_ids = action_obj.search(cr, uid, action_domain)
                    
                    # execute action
                    getattr(model_obj, method)(cr, uid, action_ids, context=context)
        
        # process output list        
        out_list = []        
        
        # build search domain
        del_search_domain = [("res_model","=",model),("active","=",False)]
      
        # check for full sync due to changed dependency        
        sync_inc = True
        lastchange = None
        if method_lastchange:            
            lastchange = method_lastchange(cr, uid, context=context)
            if lastchange:   
                for key, value in lastchange.items():
                    lastsync_lastchange_date = lastsync_lastchange.get(key)
                    if not lastsync_lastchange_date or value > lastsync_lastchange_date:
                        # TODO implement incremental                        
                        sync_inc = False
                        break
                        
        # check auto
        auto_ids = None
        auto_del_ids = None
        if auto:          
            if last_date:                
                query = ("DELETE FROM jdoc_usage "
                           " WHERE id IN ( SELECT u.id FROM jdoc_usage u "
                           "               LEFT JOIN %s t ON t.id = u.res_id AND u.res_model=%%s AND u.user_id = %%s  "
                           "               WHERE t.id IS NULL )" % model_obj._table)
                # delete unused
                cr.execute(query, (model, uid))
                    
                # check deleted only incremental
                query = ("SELECT t.id FROM %s t "
                           " INNER JOIN jdoc_usage u ON u.res_model=%%s AND u.res_id=t.id AND u.user_id=%%s AND NOT u.auto "
                           " WHERE u.auto_date > %%s " % model_obj._table)
                cr.execute(query, (model, uid, last_date))
                auto_del_ids = [r[0] for r in cr.fetchall()]
                
                if auto_del_ids:
                    
                    # query max change date
                    query = ("SELECT MAX(u.auto_date) FROM %s t "
                           " INNER JOIN jdoc_usage u ON u.res_model=%%s AND u.res_id=t.id AND u.user_id=%%s AND NOT u.auto "
                           " WHERE u.auto_date > %%s " % model_obj._table)
                
                    cr.execute(query, (model, uid, last_date))
                    res = cr.fetchone()
                    if res:
                        auto_date = res[0]
                
                    # substruct  unused ids which meet the search domain
                    if search_domain:
                        auto_search_ndomain = [("id","in",auto_del_ids)]
                        auto_search_ndomain += search_domain
                        auto_del_ignore_ids = model_obj.search(cr, uid, auto_search_ndomain)
                        if auto_del_ignore_ids:
                            auto_del_ids = list(set(auto_del_ids) - set(auto_del_ignore_ids))
            
                # include auto added
                # prepare query
                if sync_inc:
                    query = ("SELECT t.id FROM %s t "
                             " INNER JOIN jdoc_usage u ON u.res_model=%%s "
                                                    " AND u.res_id=t.id AND u.user_id=%%s "
                                                    " AND u.auto "
                                                    " AND t.write_date > %%s " % model_obj._table)                    
                    cr.execute(query, (model, uid, last_date))
                    auto_ids = [r[0] for r in cr.fetchall()]                    
                else:
                    query = ("SELECT t.id FROM %s t "
                             " INNER JOIN jdoc_usage u ON u.res_model=%%s AND u.res_id=t.id AND u.user_id=%%s AND u.auto " % model_obj._table)
                    cr.execute(query, (model, uid))                    
                    auto_ids = [r[0] for r in cr.fetchall()]
                          
      
        # only sync with last date  
        if last_date:
            # domain for search
            if sync_inc:                
                search_domain.append(("write_date",">",last_date))
                search_ndomain.append(("write_date",">",last_date))
            # domain for search deleted
            del_search_domain.append(("write_date",">",last_date))
            
            
        #
        # search changes
        #
        out_ids = model_obj.search(cr, uid, search_domain, order="write_date asc, id asc")
        if auto_ids:
            auto_domain = []
            if out_ids:
                auto_domain.append("|")
                auto_domain.append(("id","in",out_ids))
            auto_domain.append(("id","in",auto_ids))
            out_ids = model_obj.search(cr, uid, auto_domain, order="write_date asc, id asc")
        
        # resync errors
        if errors:
            for error in errors:
                oid = error.get("id")
                if oid and oid not in out_ids:
                    out_ids.append(oid)
        
        if out_ids:
            
            # get last change date
            cr.execute("SELECT MAX(write_date) FROM %s WHERE id IN %%s " % model_obj._table, (tuple(out_ids),))
            res = cr.fetchone()
            if res:
                last_date = max(last_date, res[0])
            
            # create docs
            for obj in model_obj.browse(cr, uid, out_ids, context=context):
                try:
                    doc = method_get(cr, uid, obj, options=options, context=context)
                    if doc:
                        if res_doc:
                            out_list.append(doc)
                        else:
                            out_list.append({ "id" : doc["_id"],                                 
                                              "doc" : doc 
                                            })
                except AccessError as e:
                    _logger.warning("Access Denied for read %s/%s" % (obj._model._name, obj.id))
        
        
        #
        # search deleted
        #
        
        if not first_sync:
            # process deleted
            mapping_obj.check_deleted(cr, uid, model)
            
            
            # read deleted 
            out_deleted_vals = mapping_obj.search_read(cr, uid, del_search_domain, 
                                                                ["uuid", "write_date", "res_id"],                                                             
                                                                order="write_date asc, res_id asc")
            
            # read filtered which should be deleted
            if filter_ndomain or auto_del_ids:
                # get filtered ids
                filtered_ids = []
                if filter_ndomain:
                    filtered_ids = model_obj.search(cr, uid, search_ndomain, order="write_date asc, id asc")
                if auto_del_ids:
                    filtered_ids += auto_del_ids
                # check if there are ids to delete
                if filtered_ids:
                    # get last change date
                    cr.execute("SELECT MAX(write_date) FROM %s WHERE id IN %%s " % model_obj._table, (tuple(filtered_ids),))
                    res = cr.fetchone()
                    if res:
                        last_date = max(last_date, res[0])
                    
                    # add out deleted vals
                    out_deleted_vals += mapping_obj.search_read(cr, uid, [("res_model","=",model),("active","=",True),("res_id","in",filtered_ids)], 
                                                ["uuid", "write_date", "res_id"],                                                             
                                                order="write_date asc, res_id asc")
                      
            if out_deleted_vals:
                # get last change date
                cr.execute("SELECT MAX(write_date) FROM %s WHERE res_model=%%s AND id IN %%s" % mapping_obj._table, 
                                                                    (model, tuple([v["id"] for v in out_deleted_vals]) ) ) 
                res = cr.fetchone()
                if res:            
                    last_date = max(last_date, res[0])
                    
                # get uuids
                for out_deleted_val in out_deleted_vals:
                    if not last_date or out_deleted_val["write_date"] >= last_date:
                        last_date = out_deleted_val["write_date"]
                    
                    # uuid 
                    uuid = out_deleted_val["uuid"]
                    if res_doc:
                        out_list.append({
                           "_id" : uuid,
                           "_deleted" : True                                 
                         })
                    else:
                        out_list.append({
                           "id" : uuid,
                           "deleted" : True                                 
                         })
       
       
        # after sync check for deleted
        if auto:   
            # only if last date exist       
            if last_date:
                # check for unused
                usage_obj = self.pool["jdoc.usage"]
                sliceDate = util.getNextDayOfMonth(util.currentDate(),inDay=1,inMonth=-1)
                unused_ids = usage_obj.search(cr, uid, [("res_model","=",model),("user_id","=",uid),("used","<",sliceDate),("auto","=",True)])
                if unused_ids:                   
                    usage_obj.write(cr, uid, unused_ids, {"auto" : False}, context=context)
                    cr.execute("UPDATE jdoc_usage SET auto_date=write_date WHERE id IN %s", (tuple(unused_ids),))

                # max auto_date or last_date
                if auto_date:
                    last_date = max(auto_date, last_date)
                
      
       
        # if last date is empty or it's the first sync,
        # than set current date/time as last date
        if not last_date or first_sync:
            last_date = util.currentDateTime()
        
        # create last sync
        lastsync =  {
                       "date" : last_date,
                       "seq" : seq                  
                    }
    
        if lastchange:
            lastsync["lastchange"] = lastchange
        
        res =  {
           "model" : model,
           "lastsync" : lastsync,
           "changes" : out_list,
        }
        
        if errors:
            res["errors"] = errors
        
        return res
    
    def jdoc_by_id(self, cr, uid, res_model, oid, refonly=False, options=None, context=None):
        model_obj = self.pool[res_model]
        obj = model_obj.browse(cr, uid, oid, context=context)
        if not obj:
            return False
        return self._jdoc_get(cr, uid, obj, refonly=refonly, options=options, context=context)
    
    def jdoc_get(self, cr, uid, uuid, res_model=None, refonly=False, options=None, name=None, context=None):
        mapping_obj = self.pool["res.mapping"]
        obj = mapping_obj._browse_mapped(cr, uid, uuid, res_model=res_model, name=name, context=None)
        if not obj:
            return False
        return self._jdoc_get(cr, uid, obj, refonly=refonly, options=options, context=context)
    
    def jdoc_put(self, cr, uid, doc, return_id=False, return_value=False, uuid2id_resolver=None, changed_models=None, errors=None, model=False, usage_map=None, context=None):
        if not doc:
            return False
        
        mapping_obj = self.pool.get("res.mapping")       
        
        obj_id = False
        obj = False
        res = False

        if not model:
            model = doc.get(META_MODEL)
            
        if not model:
            _logger.warning("Unable to determine model of %s" % repr(doc))
            return False

        uuid = doc.get(META_ID, False)
        if uuid:
            obj = mapping_obj._browse_mapped(cr, uid, uuid, res_model=model, context=context)
            if obj:
                model = obj._name
                obj_id = obj.id
                
        
        model_obj = self.pool[model]
        
        # get database id 
        def get_id(value, attribs):
            res = None
            res_uuid = None
            if value:
                model = attribs.get("model")
                
                # check uuid
                if isinstance(value, basestring):
                    res_uuid = value
                    res = mapping_obj.get_id(cr, uid, model, value)
                
                # check reference or document
                elif isinstance(value, dict):                                                        
                    if isReference(value):
                        # get reference
                        res_uuid = value[META_ID]
                        if not model:
                            model = value.get(META_MODEL)
                        res = mapping_obj.get_id(cr, uid, model, res_uuid)                        
                    #else: !! DANGEROUS !! 
                        # update document and get reference
                        #res = self.jdoc_put(cr, uid, value, return_id=True, changed_models=changed_models, errors=errors, context=context)
                        
            # if not found try uuid resolver
            if not res and res_uuid and uuid2id_resolver:
                res = uuid2id_resolver(res_uuid)
                
            # build usage        
            if res and usage_map:
                usage_set = usage_map.get(model, None)
                if not usage_set is None and not res in usage_set:
                    usage_set.add(res)
                    self._jdoc_access(cr, uid, model, res, context=context)
                
            return res
        
        # check for delete
        if doc.get(META_DELETE):
            try:
                with cr.savepoint():             
                    mapping_obj.unlink_uuid(cr, uid, uuid, res_model=model, context=context)
                    obj_id = False
            except Exception as e:
                if isinstance(e, AccessError):
                    _logger.warning("Access Denied for delete %s/%s" % (model, uuid))
                else:
                    _logger.exception(e);
                if not errors is None:
                    errors.append({
                       "model" : model,
                       "id" : obj_id,
                       "uuid" : uuid,
                       "error" : e.message,
                       "error_class" : e.__class__.__name__               
                    })
                else:
                    raise e
        
        # otherwise update        
        else:
        
            definition = self._jdoc_def(cr, uid, model)
            fields = definition["fields"]
            
            values = {}
            for field, value in doc.items():
                # check if it is meta field
                if isMetaField(field):
                    continue
                
                # check attribs
                attribs = fields.get(field)
                if not attribs:
                    # if no attribs exist, field not exist
                    continue
                
                dtype = attribs["dtype"]
                if dtype == "r":
                    values[field] = get_id(value, attribs)
                    
                elif dtype in ("c","l"):
                    # handle empty value
                    if not value:
                        if dtype == "l":
                            # handle one2many relation extra
                            sub_one2many = attribs.get("one2many")
                            sub_model = attribs.get("model")
                            if sub_one2many and sub_model:
                                remove_ids = self.pool[sub_model].search(cr, uid, [(sub_one2many,"=",obj_id)])
                                if remove_ids:
                                    values[field] = [(2,oid) for oid in remove_ids]
                                else:
                                    values[field] = None
                            # handle many2many
                            else:
                                values[field] = [(6,0,[])]
                        else:
                            values[field] = None
                    # handle list
                    elif isinstance(value, list):
                        if not dtype == "l":
                            raise osv.except_osv(_("Error"), _("Using list for non list type"))
                        
                        
                        sub_ids = []
                        sub_update = []
                        sub_model = attribs.get("model")
                        sub_one2many = attribs.get("one2many")
                                                
                        for list_value in value:
                            # get values
                            sub_values = None
                            if ( isinstance(list_value, dict) and not isReference(list_value) ):
                                sub_values = self.jdoc_put(cr, uid, list_value, return_value=True, model=sub_model, changed_models=changed_models, errors=errors, usage_map=usage_map, context=context)
                                
                            # get sub id
                            sub_id = get_id(list_value, attribs)
                            if sub_id:
                                sub_ids.append(sub_id)
                                if sub_values:
                                    # update
                                    sub_update.append((1,sub_id,sub_values))
                            
                            elif sub_values:
                                # create new 
                                sub_update.append((0,0,sub_values))
                                
                            # cleanup
                            if sub_one2many:
                                if obj_id:
                                    # remove unused
                                    for oid in self.pool[sub_model].search(cr, uid, [(sub_one2many,"=",obj_id)]):
                                        if not oid in sub_ids:
                                            sub_update.append((2,oid))
                            else:
                                # otherwise link many2many
                                sub_update.insert(0, (6,0,sub_ids))
                        
                        # set update                                
                        values[field] = sub_update              
                        
                else:
                    values[field] = value
                    
            if return_value:
                return values
            
            if values:        
                try:
                    with cr.savepoint():             
                        if obj_id:
                            model_obj.write(cr, uid, obj_id, values, context=context)
                        else:
                            obj_id = model_obj.create(cr, uid, values, context=context)
                except Exception as e:
                    if isinstance(e, AccessError):
                        _logger.warning("Access Denied for write %s/%s" % (model, uuid))
                    else:
                        _logger.exception(e);
                                                
                    if not errors is None:
                        errors.append({
                           "model" : model,
                           "id" : obj_id,
                           "uuid" : uuid,
                           "error" : e.message,
                           "error_class" : e.__class__.__name__               
                        })
                    else:
                        raise e
                   
            # check obj_id
            if obj_id:
                # validate, create uuid
                # use uuid passed in values if new
                uuid = mapping_obj.get_uuid(cr, uid, model, obj_id, uuid=uuid)
                
                # update updated dict
                if not changed_models is None: 
                    changed_ids =changed_models.get(model, None)
                    if changed_ids is None:
                        changed_ids = set()
                        changed_models[model]=changed_ids
                    changed_ids.add(obj_id)
                    
            

        # finished!
        if return_id:
            res = obj_id
        else:
            res = uuid
            
        return res
 
    
    def jdoc_couchdb_before(self, cr, uid, config, context=None):
        return self.jdoc_couchdb_sync(cr, uid, config, config_only=True, context=context)
    
    def jdoc_couchdb_after(self, cr, uid, config, context=None):
        return True
       
    def jdoc_couchdb_sync(self, cr, uid, config, config_only=False, context=None):
        """ Sync with CouchDB
        
            @param  config: {
                        name: "fclipboard",
                        models : [{
                            "model" : xyz
                            "view" : "_jdoc_get_fclipboard"
                            "domain" : ...
                        }]
                    }
        """
        config_name = config.get("name")
        if not config_name:
            raise osv.except_osv(_("Error"), _("No configuration name passed"))
        
        param_obj = self.pool.get("ir.config_parameter")
        db_uuid = param_obj.get_param(cr, uid, "database.uuid")
    
        # READ CONFIG      
        client_db =  "%s-%s-%s" % (config_name, db_uuid, uid)
        client_uuid = "%s-%s" % (db_uuid, uid)
        lock_id = hash(client_uuid)
        
        # lock
        cr.execute("SELECT pg_advisory_lock(%s)" % lock_id)
        try:
            # get password
            client_passwd = None
            cr.execute("SELECT password FROM res_users WHERE id=%s",(uid,))
            cr_res = cr.fetchone()
            if cr_res:
                client_passwd = cr_res[0]
            
            if not client_passwd:
                raise osv.except_osv(_("Error"), _("Unable to get user password. Deinstall 'auth_crypt' Module"))
            
            couchdb_public_url = openerp.tools.config.get("syncdb_public_url") 
            if not couchdb_public_url:
                raise osv.except_osv(_("Error"), _("No public couchdb url defined"))
            
            res = {
                "url" : couchdb_public_url,
                "db" : client_db,
                "user" : client_uuid
            } 
            
            # READ/UPDATE USER
            couchdb_url = openerp.tools.config.get("syncdb_url")
            if not couchdb_url:
                raise osv.except_osv(_("Error"), _("No couchdb url defined"))
      
            couchdb_user = openerp.tools.config.get("syncdb_user")
            couchdb_password = openerp.tools.config.get("syncdb_password")
        
            server = couchdb.Server(couchdb_url)
            if couchdb_user and couchdb_password:
                server.resource.credentials = (couchdb_user, couchdb_password)
                
            user_db = server["_users"]
            user_id = "org.couchdb.user:%s" % client_uuid
            
            user_doc = user_db.get(user_id)
            if not user_doc:
                user_doc = {
                    "_id" :  user_id,
                    "name" : client_uuid,
                    "type" : "user",
                    "roles" : []
                }
            
            user_doc["password"] = client_passwd
            user_db.save(user_doc)
            
            # CHECK RESET / DB DELETION
            if config.get("reset"):
                if client_db in server:
                    server.delete(client_db)
                return True
            
            # CREATE/OPEN DB
            db = None
            if not client_db in server:
                db = server.create(client_db)
            else:
                db = server[client_db]
                
            # UPDATE/DB SECURITY
            permissions = db.get("_security") or {"_id" : "_security" }
            members = permissions.get("members")
            names = members and members.get("names")
            if not names or not client_uuid in names:
                permissions["admins"] = {}
                permissions["members"] = {"names" : [client_uuid] }
                db.put(permissions) 
                db.commit()
            
            # CONFIG ONLY 
            if config_only:
                return res
                 
            
            # BUILD SYNC CONFIG
                   
            class SyncConfig(object):
                def __init__(self, model_config, lastsync, resync=False):
                    self.lastsync = lastsync 
                    self.readonly = model_config.get("readonly")
                    self.config = dict(model_config)
                    self.config["lastsync"] = lastsync
                    self.config["result_format"] = "doc"
                    self.config["resync"] = resync
                    self.model = model_config["model"]
                    self.seq = lastsync.get("seq", 0)
                    self.changed_revs = set()
                    self.resetChanges()
                
                def resetChanges(self):
                    self.changes = []
                    self.config["changes"] = self.changes
                
                def updateLastSync(self, lastsync):
                    self.lastsync.update(lastsync)
                    
                def getLastsync(self):
                    self.lastsync["seq"] = self.seq
                    return self.lastsync
                                
            
            # BUILD PROFILES
            syncConfigs = []
            syncConfigMap = {}
            minseq = None
            models = config.get("models")       
            resync = config.get("resync", False)
            
            # check auto and create usage
            # map if needed
            auto = config.get("auto")
            usage_map = None
            if auto:
                usage_map = {}
                for auto_model in auto:
                    usage_map[auto_model] = set()
             
            for model_config in models:
                config_uuid = "_local/lastsync_%s" % (self._get_uuid(model_config),)
                # get lastsync
                lastsync = db.get(config_uuid)
                if not lastsync:
                    lastsync = { "_id" : config_uuid }
                    
                
                # prepare config
                sc = SyncConfig(model_config, lastsync, resync)
                syncConfigs.append(sc)
                if minseq is None:
                    minseq = sc.seq
                else:
                    minseq = min(sc.seq, minseq)            
            
                syncConfigMap[sc.model] = sc
                
            
            # CHECK IF THERE ARE MODELS                  
            if minseq is None:
                return res
            
            mapping_obj = self.pool.get("res.mapping")
            
            # validate model for change
            def validateModel(change):
                doc = change["doc"]
                model = doc.get(META_MODEL)
                if not model:
                    if doc.get(META_DELETE):
                        model = mapping_obj._get_model(cr, uid, doc["_id"])
                        if model:
                            doc[META_MODEL] = model
                return model
            
            # SYNC DB        
            db_changeset = db.changes(since=minseq, include_docs=True)
            for change in db_changeset["results"]:      
                model = validateModel(change) 
                if not model:
                    continue
                
                syncConfig = syncConfigMap.get(model)
                if not syncConfig:
                    continue
                
                if syncConfig.seq >= change["seq"]:
                    continue
                
                # ADD CHANGE
                if not syncConfig.readonly:
                    syncConfig.changes.append(change)
                
            # SYNC CHANGES
            for sc in syncConfigs:
                sync_res = self.jdoc_sync(cr, uid, sc.config, usage_map=usage_map, context=context)            
                sc.updateLastSync(sync_res["lastsync"])
                sc.seq = db_changeset["last_seq"]
                
                # update documents
                changed_revs = set()
                o_changes = sync_res["changes"]
                o_conflicts = []
                            
                # SYNC BACK CHANGES
                for i, update_res in enumerate(db.update(o_changes)):
                    if update_res[0]:
                        changed_revs.add((update_res[1], update_res[2]))
                    else:        
                        o_change = o_changes[i]    
                        uuid = o_change.get("_id")
                        if uuid and uuid == update_res[1]:
                            doc = db.get(uuid)
                            if doc:
                                o_change["_rev"] = doc["_rev"]    
                                new_doc = simplejson.dumps(o_change,sort_keys=True)
                                cur_doc = simplejson.dumps(doc,sort_keys=True)
                                if new_doc != cur_doc:  
                                    o_conflicts.append(o_change)
                        else:
                            _logger.error("Sync Conflict %s -> %s " % (update_res[1],update_res[2]))
                                
                # SYNC CONFLICTS
                for update_res in db.update(o_conflicts):
                    if update_res[0]:
                        changed_revs.add((update_res[1], update_res[2]))
                    else:
                        _logger.error("Sync Conflict %s -> %s " % (update_res[1],update_res[2]))
                
                
                # FINALIZE SYNC                
                if changed_revs:           
                    # get changes                
                    sc.resetChanges()
                    # get changes again
                    db_changeset = db.changes(since=sc.seq, include_docs=True)
                    sc.seq = db_changeset["last_seq"]
                    # no sync if readonly
                    if not sc.readonly:
                        for change in db_changeset["results"]:
                            # check model
                            model = validateModel(change)
                            if not model or model != sc.model:
                                continue
                            
                            # check already process
                            already_processed = False
                            for rev_change in change["changes"]:
                                if (change["id"], rev_change["rev"]) in changed_revs:
                                    already_processed = True
                                    break
                            
                            if not already_processed:
                                sc.changes.append(change) 
                    
                    # check if changes exist
                    if sc.changes:
                        sync_res = self.jdoc_sync(cr, uid, sc.config, usage_map=usage_map, context=context)
                        sc.updateLastSync(sync_res["lastsync"])
                     
                # commit            
                cr.commit() 
                
                # update lastsync
                db.save(sc.getLastsync())
                db.commit()
                                      
            return res
        
        except:
            cr.rollback()
            raise
        
        finally:
            # unlock
            cr.execute("SELECT pg_advisory_unlock(%s)" % lock_id)
    
    @openerp.tools.ormcache()
    def _jdoc_def(self, cr, uid, model):
        return self._jdoc_create_def(cr, SUPERUSER_ID, self.pool[model])
    
    _description = "JSON Document Support"    
    _name = "jdoc.jdoc"


class jdoc_usage(osv.Model):
    
    _name = "jdoc.usage"
    _description = "JSON Document Usage"
    
    _columns = {
        "used" : fields.datetime("Used Timestamp", select=True, required=True),        
        "user_id" : fields.many2one("res.users", "User", select=True, required=True),
        "res_model" : fields.char("Resource Model", select=True, required=True),
        "res_id" : fields.integer("Resource ID", select=True, required=True),        
        "auto" : fields.boolean("Auto Sync", select=True),
        "auto_date" : fields.datetime("Auto Change", select=True)
    } 
   