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

from openerp.osv import osv

class ConfigBuilder(object):    
    """ Configuration Builder """
    def __init__(self, obj, unit=None, unit_data=None, parent=None):
        self.obj = obj
        self.parent = parent
        self.builds = []
        self.build = {}
        self.objects = {}
        self.targets = {}
        self.config = []
            
    def derive(self, obj, unit):
        return ConfigBuilder(obj, unit=unit, parent=self)
        
    def addConfigFile(self, path, mimetype, config):
        self.objects[path]=config
        self.config.append({
            "file" : path,
            "format" : mimetype
        })
    
    def close(self):
        #add objects
        if self.objects:
            self.build["objects"]=self.objects
        #add config to target
        if self.config:
            self.targets["config"]=self.config
        #add targets
        if self.targets:
            self.build["targets"]=self.targets
        
        # add build or build
        if self.parent:
            self.root.builds.append(self.build)
            
        # set 
        elif self.builds:
            self.build["units"]=self.builds
            
            

class prov_base(osv.AbstractModel):
    """ Basic Provisioning Model"""
        
    def _build(self, cr, uid, builder, context=None):
        pass
    
    def build(self, cr, uid, unit_ids, context=None):
        builder = ConfigBuilder(self)
        unit_obj = self.pool.get("posix_net.unit")
        mapping_obj = self.pool.get("res.mapping")
        view_obj = self.obj.pool.get("dataset.view")
        model_dict = {}
                
        for unit in unit_obj.browse(cr, uid, unit_ids, context=context):
            unit_type = unit.type_id
            
            # Search provisoning Model
            prov_obj = model_dict.get(unit_type.code)
            if prov_obj is None:
                prov_model_name = "prov"
                for tok in unit_type.code.split("."):
                    prov_model_name = "%s.%s" % (prov_model_name,tok)
                    prov_obj_found = self.pool.get(prov_model_name)
                    if prov_obj_found:
                        prov_obj = prov_obj_found
                model_dict[unit_type.code] = prov_obj or False
            
            
            # Do Nothing if no model was found    
            if not prov_obj:
                continue
            
            # Build
            unit_builder = builder.derive(prov_obj, unit)
            unit_uuid = mapping_obj.get_uuid(cr, uid, "posix_net.unit", unit.id)
            unit_builder.build["unit"] = view_obj.data_read(cr, uid, "posix_net.unit", unit_uuid)
            prov_obj._build(cr, uid, unit_builder, context=context)
            unit_builder.close()
              
        builder.close()      
        return builder.build
    
    _name = "prov.base"
    _description = "Basic Builder"
    

class prov_router_wlan(osv.AbstractModel):
    """ Basic Provisioning for WLAN Router """
    _name = "prov.router.wlan"
    _inherit = "prov.base"
    _description = "Basic WLAN Router"
    
    
class prov_config(osv.AbstractModel):
    """ Basic Provisioning for Config """
    _name = "prov.config"
    _inherit = "prov.base"
    _description = "Basic Config Provisioning"
    