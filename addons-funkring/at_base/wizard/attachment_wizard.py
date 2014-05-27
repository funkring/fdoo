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
import os
import yaml
import base64

class attachment_import(osv.TransientModel):
    
    def do_import(self,cr,uid,ids,context=None):
        attachment_obj = self.pool.get("ir.attachment")
        for rec in self.browse(cr, uid, ids, context):
            folder = rec.folder
            for name in os.listdir(folder):
                if not name.endswith(".yaml"):
                    model_dir = os.path.join(folder, name)
                    if os.path.isdir(model_dir):
                        yaml_dir = model_dir + ".yaml"
                        if os.path.isdir(yaml_dir):
                            for rec in os.listdir(yaml_dir):
                                if rec.endswith(".yaml"):
                                    bin_file = "%s.bin" % (rec.split(".")[0],)
                                    bin_file = os.path.join(model_dir,bin_file)
                                    yaml_file = os.path.join(yaml_dir,rec)
                                    
                                    values = None
                                    fp = file(yaml_file, "rb")
                                    try:
                                        values = yaml.load(fp)
                                    finally:
                                        fp.close()
                                    
                                    fp = file(bin_file,"rb")
                                    try:
                                        bin_data = fp.read()
                                        values["file_size"]=len(bin_data)
                                        values["datas"] = base64.encodestring(bin_data)                                                 
                                    finally:                    
                                        fp.close()
                                    
                                    attachment_obj.create(cr, uid, values, context)           
        return { "type" : "ir.actions.act_window_close" }                      
                     
    
    _name="attachment.import"
    _description = "Attachment Export"
    _columns = {
        "folder" : fields.char("Folder",size=255,required=True)
    }    
attachment_import()



class attachment_export(osv.osv_memory):
    
    def do_export(self, cr, uid, ids, context=None):
        attachment_obj = self.pool.get("ir.attachment")         
        for rec in self.browse(cr, uid, ids, context):
            ids = attachment_obj.search(cr,uid,[])
            fields = ["id","name","datas","datas_fname","res_name","res_model","res_id"]
            folder = rec.folder            
            for oid in ids:         
                file_rec = attachment_obj.read(cr,uid,oid,fields,context=context)
                res_model = file_rec.get("res_model")
                file_id = file_rec.get("id")
                file_data = file_rec.get("datas")                
                if res_model and file_data:
                    del file_rec["datas"]                                        
                    model_path = os.path.join(folder,res_model)
                    yaml_path = os.path.join(folder,res_model + ".yaml")
                    
                    if not os.path.exists(model_path):
                        os.makedirs(model_path)
                        
                    if not os.path.exists(yaml_path):
                        os.makedirs(yaml_path)
                    
                    yaml_file = os.path.join(yaml_path,"%d.yaml" % (file_id,))
                    export_file = os.path.join(model_path,"%d.bin" % (file_id,))
                                                           
                    fp = file(yaml_file, "wb+")
                    try:
                        yaml.dump(file_rec,fp)
                    finally:
                        fp.close()
                    
                    fp = file(export_file,"wb+")
                    try:
                        fp.write(base64.decodestring(file_data))                        
                    finally:                    
                        fp.close()
        return { "type" : "ir.actions.act_window_close" }
    
    _name="attachment.export"
    _description = "Attachment Import"
    _columns = {
        "folder" : fields.char("Folder",size=255,required=True)
    }
