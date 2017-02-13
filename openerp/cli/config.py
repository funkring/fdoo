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

from openerp import tools
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
        
        self.parser.add_argument("--debug", action="store_true")
        
        self.parser.add_argument("--lang", required=False, 
                                 help="Language (Default is %s)" % config.defaultLang)
    
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
            
        if params.db_user:
            config_args.append("--db_user")
            config_args.append(params.db_user)
            
        if params.addons_path:
            config_args.append("--addons-path")
            config_args.append(params.addons_path)
            
        if params.lang:
            config_args.append("--lang")
            config_args.append(params.lang)
        
        config.parse_config(config_args)
        self.params = params
        self.run_config()
        
    def run_config(self):
        _logger.info("Nothing to do!")
        
    def run_config_env(self):
        _logger.info("Nothing to do!")
         
    def setup_env(self):
        # setup pool    
        self.pool = RegistryManager.get(self.params.database)
        self.cr = self.pool.cursor()
        try:
            # create environment
            with api.Environment.manage():
                self.env = openerp.api.Environment(self.cr, 1, {})
                self.run_config_env()
                    
            self.cr.commit()    
        except Exception, e:
            if self.params.debug:
                _logger.exception(e)
            else:
                _logger.error(e)
        finally:
            self.cr.rollback()
            self.cr.close()


class Update(ConfigCommand):
    """ Update Module/All """

    def run_config(self):
        if self.params.module:
            config["update"][self.params.module]=1
        else:
            config["update"]["all"]=1
        RegistryManager.get(self.params.database, update_module=True)
        
        
class Po_Export(ConfigCommand):
    """ Export *.po File """
    
    def run_config(self):
        # check module
        if not self.params.module:
            _logger.error("No module defined for export!")
            return
        # check path
        self.modpath = openerp.modules.get_module_path(self.params.module)
        if not self.modpath:
            _logger.error("No module %s not found in path!" % self.params.module)
            return
       
        # check lang
        self.lang = self.params.lang or config.defaultLang
        self.langfile = self.lang.split("_")[0] + ".po"
        self.langdir = os.path.join(self.modpath,"i18n")
        if not os.path.exists(self.langdir):
            _logger.warning("Created language directory %s" % self.langdir)
            os.mkdir(self.langdir)
        
        # run with env
        self.setup_env()
      
    def run_config_env(self):
        # check module installed
        self.model_obj = self.pool["ir.module.module"]
        if not self.model_obj.search_id(self.cr, 1, [("state","=","installed"),("name","=",self.params.module)]):
            _logger.error("No module %s installed!" % self.params.module)
            return 
        
        export_filename = os.path.join(self.langdir, self.langfile)
        export_f = file(export_filename,"w")
        try:
            _logger.info('Writing %s', export_filename)
            tools.trans_export(self.lang, [self.params.module], export_f, "po", self.cr)
        finally:
            export_f.close()
        
class Po_Import(Po_Export):
    """ Import *.po File """
    
    def __init__(self):
        super(Po_Import, self).__init__()
        self.parser.add_argument("--overwrite", action="store_true", default=True, help="Override existing translations")
    
    def run_config_env(self):
        # check module installed
        self.model_obj = self.pool["ir.module.module"]
        if not self.model_obj.search_id(self.cr, 1, [("state","=","installed"),("name","=",self.params.module)]):
            _logger.error("No module %s installed!" % self.params.module)
            return 
        
        import_filename = os.path.join(self.langdir, self.langfile)
        if not os.path.exists(import_filename):
            _logger.error("File %s does not exist!" % import_filename)
            return 
        
        # import 
        context = {'overwrite': self.params.overwrite }
        if self.params.overwrite:
            _logger.info("Overwrite existing translations for %s/%s", self.params.module, self.lang)
        openerp.tools.trans_load(self.cr, import_filename, self.lang, module_name=self.params.module, context=context)  

        
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
    
    
    def cleanup_translation(self):
        self.cr.execute("SELECT id, lang, name, res_id, module FROM ir_translation WHERE type='model' ORDER BY lang, module, name, res_id, id")
        refs = {}
        
        for row in self.cr.fetchall():
            # get name an res id
            name = row[2] and row[2].split(",")[0] or None
            res_id = row[3]            
            if name and res_id:
                ref = (name, res_id)
                ref_valid = False
                
                if ref in refs:
                    ref_valid = refs.get(ref)
                else:
                    model_obj = self.pool.get(name)
                    
                    # ignore uninstalled modules
                    if not model_obj or not model_obj._table:
                        continue
                    
                    self.cr.execute("SELECT COUNT(id) FROM %s WHERE id=%s" % (model_obj._table, res_id))
                    if self.cr.fetchone()[0]:
                        ref_valid = True
                        
                    refs[ref] = ref_valid
                    
                # check if it is to delete
                if not ref_valid:
                    self.fixable("Translation object %s,%s no exist" % (name, res_id))
                    self.cr.execute("DELETE FROM ir_translation WHERE id=%s", (row[0],))
            
    
    def cleanup_double_translation(self):
        # check model translations
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
        
        # check view translations    
        self.cr.execute("SELECT id, lang, name, src, module FROM ir_translation WHERE type='view' AND res_id=0 ORDER BY lang, module, name, src, id")
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
        self.cr.execute("DELETE FROM ir_model_data WHERE model='ir.module.module' AND res_id=%s", (module.id,))
        
    def cleanup_model_data(self):
        self.cr.execute("SELECT d.id, d.model, d.res_id, d.name FROM ir_model_data d "
                        " INNER JOIN ir_module_module m ON  m.name = d.module AND m.state='installed' "
                        " WHERE d.res_id > 0 ")
        
        for oid, model, res_id, name in self.cr.fetchall():
            model_obj = self.pool[model]
            
            deletable = False
            if not model_obj:                
                deletable = True
            else:
                self.cr.execute("SELECT id FROM %s WHERE id=%s" % (model_obj._table, res_id))
                if not self.cr.fetchall():                   
                    deletable = True
                    
            if deletable:
                self.fixable("ir.model.data %s/%s (%s) not exist" %  (model, res_id, name))
                self.cr.execute("DELETE FROM ir_model_data WHERE id=%s" % oid)
        
    def cleanup_modules(self):
        module_obj = self.pool["ir.module.module"]
        module_ids = module_obj.search(self.cr, SUPERUSER_ID, [])
        for module in module_obj.browse(self.cr, SUPERUSER_ID, module_ids):
            info = openerp.modules.module.load_information_from_description_file(module.name)
            if not info:
                self.delete_module(module)

        # check invalid module data
        self.cr.execute("SELECT id, res_id, name FROM ir_model_data WHERE model='ir.module.module' AND res_id > 0")
        for model_data_id, module_id, name in self.cr.fetchall():
            module_name = name[7:]
            self.cr.execute("SELECT id FROM ir_module_module WHERE id=%s",(module_id,))
            res = self.cr.fetchone()
            if not res:
                self.fixable("Module %s for module data %s not exist" % (module_name, model_data_id))
                self.cr.execute("DELETE FROM ir_model_data WHERE id=%s", (model_data_id,))

                
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
                    self.cleanup_model_data()    
                    self.cleanup_translation()            
                    
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
            
            
class RemoveTestData(ConfigCommand):
    
        
    def delete_invoice(self):
        # reset move lines
        _logger.info("reset account_move_line to 'draft'")
        self.cr.execute("UPDATE account_move_line SET state='draft'")
        
        # reset moves
        _logger.info("reset account_move to 'draft'")
        self.cr.execute("UPDATE account_move SET state='draft'")

        # remove concilations
        reconcile_obj = self.env["account.move.reconcile"]
        self.cr.execute("SELECT id FROM account_move_reconcile")
        reconcile_ids = [r[0] for r in self.cr.fetchall()]
        for reconcile in reconcile_obj.browse(reconcile_ids):
            _logger.info("delete reconcile %s " % reconcile.name) 
            reconcile.unlink()
            
        # unlink invoices
        self.cr.execute("SELECT id FROM account_invoice")
        invoice_ids = [r[0] for r in self.cr.fetchall()]        
        invoice_obj = self.env["account.invoice"]
        for inv in invoice_obj.browse(invoice_ids):
            _logger.info("delete invoice %s " % inv.name)            
            inv.internal_number = None
            inv.delete_workflow()
            inv.state="draft"            
            inv.unlink()
            
        # unlink moves
        self.cr.execute("SELECT id FROM account_move")
        move_ids = [r[0] for r in self.cr.fetchall()]
        move_obj = self.env["account.move"]
        for move in  move_obj.browse(move_ids):
            _logger.info("delete move %s" % move.name)
            move.unlink()
            
        # unlink vouchers
        voucher_obj = self.env["account.voucher"]
        self.cr.execute("SELECT id FROM account_voucher")
        voucher_ids = [r[0] for r in self.cr.fetchall()]
        for voucher in voucher_obj.browse(voucher_ids):
            _logger.info("delete voucher %s " % voucher.id) 
            voucher.cancel_voucher()
            voucher.unlink()
     
    
    def delete_procurement(self):
        proc_obj = self.env["procurement.order"]
        self.cr.execute("SELECT id FROM procurement_order")
        proc_ids = [r[0] for r in self.cr.fetchall()]        
        for proc in proc_obj.browse(proc_ids):
            _logger.info("delete procurement %s " % proc.name)
            proc.state="cancel"
            proc.unlink()
    
    def delete_stock(self):
        move_obj = self.env["stock.move"]
        
        _logger.info("reset stock move to 'draft'")
        self.cr.execute("UPDATE stock_move SET state='draft'")
        
        self.cr.execute("SELECT id FROM stock_move")        
        move_ids = [r[0] for r in self.cr.fetchall()                    ]        
        for move in move_obj.browse(move_ids):
            _logger.info("delete stock move %s " % move.name)
            move.unlink()
            
        quant_obj = self.env["stock.quant"]
        self.cr.execute("SELECT id FROM stock_quant")        
        quant_ids = [r[0] for r in self.cr.fetchall()]
        for quant in quant_obj.browse(quant_ids):
            _logger.info("delete quant %s " % quant.name)
            quant.unlink()
            
        pack_obj = self.env["stock.pack.operation"]
        self.cr.execute("SELECT id FROM stock_pack_operation")
        pack_ids = [r[0] for r in self.cr.fetchall()]
        for pack in pack_obj.browse(pack_ids):
            _logger.info("delete pack operation %s " % pack.id)
            pack.unlink()
            
        picking_obj = self.env["stock.picking"]
        self.cr.execute("SELECT id FROM stock_picking")
        picking_ids = [r[0] for r in self.cr.fetchall()]
        for picking in picking_obj.browse(picking_ids):
            _logger.info("delete picking %s" % picking.name)
            picking.action_cancel()
            picking.delete_workflow()
            picking.unlink()
            
    def delete_purchase(self):
        purchase_obj = self.env["purchase.order"]
        self.cr.execute("SELECT id FROM purchase_order")
        purchase_ids = [r[0] for r in self.cr.fetchall()]        
        for purchase in purchase_obj.browse(purchase_ids):
            _logger.info("delete purchase %s " % purchase.name)
            purchase.delete_workflow()
            purchase.state="cancel"
            purchase.unlink()
    
    def delete_hr(self):
        _logger.info("delete hr_attendance")
        self.cr.execute("DELETE FROM hr_attendance")
        
        timesheet_obj = self.env["hr_timesheet_sheet.sheet"]
        self.cr.execute("SELECT id FROM hr_timesheet_sheet_sheet")
        sheet_ids = [r[0] for r in self.cr.fetchall()]
        for sheet in timesheet_obj.browse(sheet_ids):
            _logger.info("delete sheet %s" % sheet.id)
            sheet.delete_workflow()
            sheet.state="draft"
            sheet.unlink()
       
        expense_obj = self.env["hr.expense.expense"]
        self.cr.execute("SELECT id FROM hr_expense_expense")
        expense_ids = [r[0] for r in self.cr.fetchall()]
        for expense in expense_obj.browse(expense_ids):
            _logger.info("delete expense %s" % expense.name)
            expense.unlink()
    
    def delete_sale(self):
        # delete analytic lines
        self.cr.execute("DELETE FROM account_analytic_line")
        deleted_task = set()
        deleted_proj = set()
                
        # delete tasks
        def delete_task(tasks):
            for task in tasks:
                if not task.id in deleted_task:
                    deleted_task.add(task.id)
                    delete_task(task.child_ids)
                    _logger.info("delete task %s" % task.name)
                    task.unlink()
            
        # delete project
        def delete_project(proj):
            if not proj.id in deleted_proj:
                deleted_proj.add(proj.id)
                delete_task(project.tasks)
                _logger.info("delete project %s" % project.name)
                project.unlink()
                    
        # delete task without project
        task_obj = self.env["project.task"]
        self.cr.execute("SELECT id FROM project_task WHERE project_id IS NULL")
        task_ids = [r[0] for r in self.cr.fetchall()]
        delete_task(task_obj.browse(task_ids))
              
        
              
        # delete project which are subproject form first default project
        project_obj = self.env["project.project"] 
        projects = project_obj.search([("parent_id","=",1)])
        for project in projects:            
            delete_project(project)
        
        # delete order and projects
        sale_obj = self.env["sale.order"]
        self.cr.execute("SELECT id FROM sale_order")
        order_ids = [r[0] for r in self.cr.fetchall()]        
        for order in sale_obj.browse(order_ids):
            _logger.info("delete sale order %s" % order.name)
            order.action_cancel()
            project = order.order_project_id
            if project:
                delete_project(project)
            order.unlink()
    
    def run_config_env(self):
        self.delete_invoice()
        self.delete_procurement()
        self.delete_stock()
        self.delete_purchase()
        self.delete_sale()
        self.delete_hr()
    
    def run_config(self):
        self.setup_env()
