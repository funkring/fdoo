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


import logging
import openerp
import argparse
import os

from openerp import api
from openerp.tools.config import config
from openerp.modules.registry import RegistryManager
from . import Command

# Also use the `openerp` logger for the main script.

_logger = logging.getLogger('openerp')

from openerp import SUPERUSER_ID

def required_or_default(name, h):
    """
    Helper to define `argparse` arguments. If the name is the environment,
    the argument is optional and draw its value from the environment if not
    supplied on the command-line. If it is not in the environment, make it
    a mandatory argument.
    """
    d = None
    if os.environ.get("ODOO" + name.upper()):
        d = {"default": os.environ["ODOO" + name.upper()]}
    else:
        # default addon path
        if name=="ADDONS":
            cli_dir = os.path.dirname(os.path.realpath(__file__))
            addons_path = os.path.realpath(os.path.join(cli_dir,
                                                            "..",
                                                            "..",
                                                            "config",
                                                            "enabled-addons",
                                                            "openerp",
                                                            "addons"))
            if os.path.exists(addons_path):
                d = {"default" : addons_path }
                    
        if not d:
            d = {"required": True}
            
    d["help"] = h + ". The environment variable ODOO" + \
                name.upper() + " can be used instead."
    return d


class ConfigCommand(Command):
    """ Basic Config Command """
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Odoo Config")
        self.parser.add_argument("--addons-path", metavar="ADDONS",
                                 **required_or_default("ADDONS",
                                 "colon-separated list of paths to addons"))
                        
        self.parser.add_argument("--database", metavar="DATABASE",
                                 **required_or_default("DATABASE",
                                "the database to modify"))
            
        self.parser.add_argument("-m", "--module", metavar="MODULE", required=False)
        self.parser.add_argument("--default-lang",required=False)
        
        self.parser.add_argument("--pg_path", metavar="PG_PATH", help="specify the pg executable path")    
        self.parser.add_argument("--db_host", metavar="DB_HOST", default=False,
                             help="specify the database host")
        self.parser.add_argument("--db_password", metavar="DB_PASSWORD", default=False,
                             help="specify the database password")
        self.parser.add_argument("--db_port", metavar="DB_PORT", default=False,
                             help="specify the database port", type=int)
        self.parser.add_argument("--db_user", metavar="DB_USER", default=False,
                            help="specify the database user")
    
    def run(self, args):  
        params = self.parser.parse_args(args)
        
        config_args = []
        
        if params.database:
            config_args.append("--database")
            config_args.append(params.database)
            
        if params.module:
            config_args.append("--module")
            config_args.append(params.module)
            
        if params.default_lang:
            config_args.append("--default-lang")
            config_args.append(params.default_lang)
            
        if params.pg_path:
            config_args.append("--pg_path")
            config_args.append(params.pg_path)
            
        if params.db_host:
            config_args.append("--db_host")
            config_args.append(params.db_host)
            
        if params.db_password:
            config_args.append("--db_password")
            config_args.append(params.db_password)
            
        if params.db_port:
            config_args.append("--db_port")
            config_args.append(params.db_port)
            
        if params.db_port:
            config_args.append("--db_user")
            config_args.append(params.db_user)
            
        if params.addons_path:
            config_args.append("--addons-path")
            config_args.append(params.addons_path)
        
        config.parse_config(config_args)
        self.params = params
        self.run_config()
        
    def run_config(self):
        _logger.info("Nothing to do!")


class Update(ConfigCommand):
    """ Update Module/All """

    def run_config(self):
        if self.params.module:
            config["update"][self.params.module]=1
        else:
            config["update"]["all"]=1
        RegistryManager.get(self.params.database, update_module=True)
        
        
class CleanUp(ConfigCommand):
    """ CleanUp Database """
    
    def __init__(self):
        super(CleanUp, self).__init__()
        self.parser.add_argument("--fix", action="store_true", help="Do/Fix all offered cleanup")
        self.parser.add_argument("--full", action="store_true", help="Intensive cleanup")
        self.clean=True
    
    def fixable(self, msg):
        self.clean=False
        if self.params.fix:
            _logger.info("[FIX] %s" % msg)
        else:
            _logger.warning("[FIXABLE] %s" % msg)
    
    def notfixable(self, msg):
        self.clean=False
        _logger.warning("[MANUAL FIX] %s" % msg)
    
    def cleanup_double_translation(self):
        self.cr.execute("SELECT id, lang, name, res_id, module FROM ir_translation WHERE type='model' ORDER BY lang, module, name, res_id, id")
        last_key = None
        first_id = None
        for row in self.cr.fetchall():
            key = row[1:]
            if last_key and cmp(key,last_key) == 0:                
                self.fixable("Double Translation %s for ID %s" % (repr(row), first_id))
                self.cr.execute("DELETE FROM ir_translation WHERE id=%s", (row[0],))
            else:
                first_id = row[0]
            last_key = key
            
        # show manual fixable
        self.cr.execute("SELECT id, lang, name, res_id FROM ir_translation WHERE type='model' AND NOT name LIKE 'ir.model%' ORDER BY lang, name, res_id, id")
        last_key = None
        first_id = None
        for row in self.cr.fetchall():
            key = row[1:]
            if last_key and cmp(key,last_key) == 0:                
                self.notfixable("Double Translation %s for ID %s" % (repr(row), first_id))
            else:
                first_id = row[0]
            last_key = key
            
            
    def delete_model(self, model):
        self.deleted_models[model.id]=model.model
        self.fixable("Delete model %s,%s" % (model.model, model.id))
        
        model_constraint_obj = self.pool["ir.model.constraint"]
        constraint_ids = model_constraint_obj.search(self.cr, SUPERUSER_ID, [("model","=",model.id)])
        for constraint in model_constraint_obj.browse(self.cr, SUPERUSER_ID, constraint_ids):
            self.fixable("Delete model constraint %s,%s" % (constraint.name, constraint.id))
            constraint.unlink()
        
        model_access_obj = self.pool["ir.model.access"]
        access_ids = model_access_obj.search(self.cr, SUPERUSER_ID, [("model_id","=",model.id)])
        for access in model_access_obj.browse(self.cr, SUPERUSER_ID, access_ids):
            self.fixable("Delete model access %s,%s" % (access.name, access.id))
            access.unlink()
        
        model_rel_obj = self.pool["ir.model.relation"]
        rel_ids = model_rel_obj.search(self.cr, SUPERUSER_ID, [("model","=",model.id)])
        for rel in model_rel_obj.browse(self.cr, SUPERUSER_ID, rel_ids):
            self.fixable("Delete model relation %s,%s" % (rel.name, rel.id))
            rel.unlink()
            
        model_data_obj = self.pool["ir.model.data"]
        data_ids = model_data_obj.search(self.cr, SUPERUSER_ID, [("model","=",model.model)])
        for data in model_data_obj.browse(self.cr, SUPERUSER_ID, data_ids):
            self.fixable("Delete model data %s,%s" % (data.name,data.id))
            data.unlink()
        
        model_field_obj = self.pool["ir.model.fields"]
        field_ids = model_field_obj.search(self.cr, SUPERUSER_ID, [("model_id","=",model.id)])
        for field in model_field_obj.browse(self.cr, SUPERUSER_ID, field_ids):
            self.fixable("Delete model field %s,%s" % (field.name, field.id))
            self.cr.execute("DELETE FROM ir_model_fields WHERE id=%s",(field.id,))
        
        self.cr.execute("SELECT id, name, type FROM ir_translation WHERE type IN ('model','field','view') AND name LIKE '%s%%'" % model.model)
        for oid, name, t in self.cr.fetchall():
            self.fixable("Delete model translation {id:%s|name:%s|type:%s}" % (oid, name, t))
            self.cr.execute("DELETE FROM ir_translation WHERE id=%s", (oid,))
        
        self.cr.execute("DELETE FROM ir_model WHERE id=%s", (model.id,))
        
    def delete_model_data(self, model_data):
        self.fixable("Delete model_data %s,%s,%s,%s" % (model_data.name,model_data.id,model_data.model,model_data.res_id))
        model_obj = self.pool.get(model_data.model)
        if model_obj:
            self.fixable("Delete %s,%s" % (model_obj._name,model_data.res_id))
            model_obj.unlink(self.cr, SUPERUSER_ID, [model_data.res_id])
        model_data.unlink()
            
    def delete_module(self, module):
        self.deleted_modules[module.id]=module.name
        self.fixable("Delete module %s,%s" % (module.name,module.id))
        self.cr.execute("UPDATE ir_module_module SET state='uninstalled' WHERE id=%s", (module.id,))
        
        model_data_obj = self.pool["ir.model.data"]
        model_data_ids = model_data_obj.search(self.cr, SUPERUSER_ID, [("module","=",module.name)])
        
        for model_data in model_data_obj.browse(self.cr, SUPERUSER_ID, model_data_ids):            
            self.delete_model_data(model_data)
            
        self.cr.execute("DELETE FROM ir_module_module_dependency WHERE name=%s OR module_id=%s", (module.name, module.id))
        self.cr.execute("DELETE FROM ir_module_module WHERE id=%s", (module.id,))
        
    def cleanup_modules(self):
        module_obj = self.pool["ir.module.module"]
        module_ids = module_obj.search(self.cr, SUPERUSER_ID, [])
        for module in module_obj.browse(self.cr, SUPERUSER_ID, module_ids):
            info = openerp.modules.module.load_information_from_description_file(module.name)
            if not info:
                self.delete_module(module)
                
#     def cleanup_properties(self):
#         self.cr.execute("SELECT name, type, value_reference FROM ir_property WHERE NOT company_id IS NULL AND ")
#         for 
        
    def cleanup_models(self):
        model_obj = self.pool["ir.model"]        
        model_ids = model_obj.search(self.cr, SUPERUSER_ID, [])
        for model in model_obj.browse(self.cr,1, model_ids):
            if not self.pool.get(model.model):
                self.delete_model(model)
        
    def run_config(self):
        self.deleted_modules = {}
        self.deleted_models = {}
        
        # check full cleanup
        if self.params.full:
            
            # create registry
            self.pool = RegistryManager.get(self.params.database, update_module=True)
            self.cr = self.pool.cursor()
            # set auto commit to false
            self.cr.autocommit(False)
            
            try:
                
                # create environment
                with api.Environment.manage():

                    self.cleanup_models()
                    self.cleanup_modules()                    
                    
                    if self.params.fix:
                        self.cr.commit()
                        
            except Exception, e:
                _logger.error(e)
                return
            finally:
                self.cr.rollback()
                self.cr.close()
        
        # open database
        db = openerp.sql_db.db_connect(self.params.database)
        
        # basic cleanup's
        self.cr = db.cursor()
        self.cr.autocommit(False)
        try:         
            self.cleanup_double_translation()            
            if self.params.fix:
                self.cr.commit()
        except Exception, e:
            _logger.error(e)
            return
        finally:
            self.cr.rollback()
            self.cr.close()
            self.cr = None
            
        if self.clean:
            _logger.info("Everything is CLEAN!")
        else:
            _logger.warning("Cleanup necessary")
            
      
    