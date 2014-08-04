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


from . import common2


def run(args):
    import openerp.tools.config
    from openerp.modules import module
    import os
    import logging
    from lxml import etree
    import re

    #init logger
    logger = logging.getLogger('cleanup')
    #init args
    common2.set_common_server(args)

    config = openerp.tools.config
    modules = set()
    xmlid_dict = dict()
    xmlid_set = set()

    # get modules
    for path in config['addons_path'].split(","):
        for name in  os.listdir(path):
            module_path = os.path.join(path,name)
            if os.path.isdir(module_path) and os.path.exists(os.path.join(module_path,"__openerp__.py")):
                module_info = module.load_information_from_description_file(name, module_path)
                if module_info:
                    modules.add(name)
                    data_files = []

                    # add data files
                    for file_spec in ("data","init_xml","update_xml"):
                        xml_files = module_info.get(file_spec)
                        if xml_files:
                            data_files.extend(xml_files)

                    for data_file in data_files:
                        data_file_path = os.path.join(module_path, data_file)
                        if data_file.lower().endswith(".xml"):
                            try:
                                doc = etree.parse(data_file_path).getroot()
                                for data_doc in doc.findall("data"):
                                    if len(data_doc):
                                        #noupdate =  data_doc.get("noupdate") == "1"
                                        for element in data_doc:
                                            element_id = element.attrib.get("id")
                                            if element_id:
                                                element_module = name

                                                # check if module is passed
                                                tk =  element_id.split(".")
                                                if len(tk) == 2:
                                                    element_module=tk[0]
                                                    element_id=tk[1]

                                                xmlid_modules = xmlid_dict.get(element_id)
                                                if not xmlid_modules:
                                                    xmlid_modules=[]
                                                    xmlid_dict[element_id]=xmlid_modules
                                                if element_module not in xmlid_modules:
                                                    xmlid_modules.append(element_module)

                                                xmlid_key = (element_module,element_id)
                                                xmlid_set.add(xmlid_key)
                            except Exception,e:
                                logger.error("Unable to parse file %s" % data_file_path)
                                raise e


    # cleanup old model data
    db = openerp.sql_db.db_connect(args.database)
    cr = db.cursor()
    try:
        # cleanup invalid resource data
        cr.execute("SELECT id, module, model, res_id FROM ir_model_data WHERE res_id=0")
        for oid, module_name, model, res_id in cr.fetchall():
            logger.info("Delete model data [%s] %s/%s/%s" % (oid, module_name, model, res_id))
            cr.execute("DELETE FROM ir_model_data WHERE id = %s" % oid)

        # delete unused
        model2table = {
           "ir.actions.act_window" : "ir_act_window",
           "ir.actions.act_window.view" : "ir_act_window_view" ,
           "workflow" : "wkf",
           "workflow.transition" : "wkf_transition",
           "workflow.activity" : "wkf_activity",
           "ir.actions.report.xml" : "ir_act_report_xml"
        }

        def get_childs(table, parent_id, ids=[]):
            ids.append(parent_id)
            #
            cr.execute("SELECT id FROM %s WHERE parent_id=%s" % (table, parent_id))
            child_ids = [r[0] for r in cr.fetchall()]
            for child_id in child_ids:
                get_childs(table, child_id, ids)
            return ids

        def delete_all(table, parent_id):
            ids = get_childs(table, parent_id)
            ids.reverse()
            for oid in ids:
                cr.execute("DELETE FROM %s WHERE id=%s" % (table, oid))

        def delete_model_data(oid, module_name, model, res_id):
            if not args.fix:
                return

            table = model2table.get(model)
            if not table:
                table = model.replace(".","_")

            # special handling for models
            if model == "ir.model":
                return
#                 cr.execute("DELETE FROM ir_rule WHERE model_id = %s",(res_id,))
#                 cr.execute("DELETE FROM ir_model_constraint WHERE model = %s",(res_id,))
#                 cr.execute("DELETE FROM ir_model_relation WHERE model = %s",(res_id,))
            if model == "ir.ui.menu":
                delete_all(table, res_id)

            logger.info("Delete model data [%s] %s/%s/%s" % (oid, module_name, model, res_id))

            # delete resources
            delete_stmt = "DELETE FROM %s WHERE id = %s" % (table, res_id)
            cr.execute(delete_stmt)
            # delete data
            cr.execute("DELETE FROM ir_model_data WHERE id = %s", (oid,) )


        # correct xmlids
        xmlid_exclude = re.compile("trans_.*|chart[0-9]+.*|module_install_notification",re.IGNORECASE)
        cr.execute("SELECT id, module, model, res_id, name, noupdate FROM ir_model_data")
        for oid, module, model, res_id, xmlid, noupdate in cr.fetchall():
            xmlid_key = (module,xmlid)
            if not noupdate:
                if not xmlid_key in xmlid_set and model in ('ir.ui.view','ir.actions.act_window'):
                    logger.info("[FIXABLE] XML record [%s] could be deleted" % (xmlid,))
                    delete_model_data(oid, module, model, res_id)

            xmlid_modules = xmlid_dict.get(xmlid)
            if xmlid_modules:
                if not module in xmlid_modules:
                    if xmlid_exclude.match(xmlid):
                        if args.verbose:
                            logger.warning("[IGNORED] XML record [%s] ignored!" % (xmlid,))
                    elif len(xmlid_modules) == 1:
                        moved_to_module = xmlid_modules[0]
                        logger.info("[FIXABLE] XML record [%s] moved from module [%s] to module [%s]" % (xmlid, module, moved_to_module))
                        if args.fix:
                            cr.execute("SELECT id FROM ir_model_data WHERE module=%s AND name=%s", (moved_to_module, xmlid))
                            rows = cr.fetchall()

                            # check if there alreade exist one, if exist delete current
                            if len(rows):
                                cr.execute("DELETE FROM ir_model_data WHERE id=%s", (oid,))
                                logger.info("Deleted XML record [%s] from module [%s], because it exist already on for module [%s]" % (xmlid, module, moved_to_module))
                            # if not move
                            else:
                                logger.info("Moved XML record [%s] from module [%s] to module [%s]" % (xmlid, module, moved_to_module))
                                cr.execute("UPDATE ir_model_data SET module=%s WHERE id=%s", (moved_to_module, oid))

                    elif len(xmlid_modules) > 1:
                        logger.warning("[UNFIXABLE] XML record [%s] has moved from [%s] in one of this modules [%s], or something else!" % (xmlid, module, ",".join(xmlid_modules)))

        # delete all from removed modules
        cr.execute("SELECT id, module, model, res_id FROM ir_model_data WHERE module NOT IN %s" % (tuple(modules),))
        for oid, module_name, model, res_id in cr.fetchall():
            delete_model_data(oid, module_name, model, res_id)

#         # cleanup window actions left behind
#         cr.execute("SELECT w.id, w.name, md.id, md.module, md.name FROM ir_act_window w "
#                    " INNER JOIN ir_model_data md on md.model = 'ir.actions.act_window' AND md.res_id = w.id AND md.noupdate = false "
#                    " WHERE w.res_id IS NULL")
#
#         for act_id, act_name, oid, module, name in cr.fetchall():
#             logger.info("[FIXABLE] Windows Action: [%s] '%s' with resource [%s] in module [%s] and name [%s] could be deleted" % (act_id, act_name, oid, module, name))
#             delete_model_data(oid, module, 'ir.actions.act_window', act_id)

        cr.commit()
    except Exception, e:
        logger.error(e)
        return
    finally:
        cr.close()


    # do full update?
    if args.full:

        # load and update registry
        registry = openerp.modules.registry.RegistryManager.get(
            args.database, update_module=True)
        cr = registry.db.cursor() # TODO context manager

        # process further cleanup
        try:
            module_obj = registry.get('ir.module.module')
            model_obj = registry.get('ir.model')

            modules_to_delete = {}
            for module in module_obj.browse(cr,1,module_obj.search(cr, 1,[])):
                info = openerp.modules.module.load_information_from_description_file(module.name)
                if not info:
                    modules_to_delete[module.id]=module.name

            for oid,name in modules_to_delete.items():
                logger.info("Delete module [%s] %s" % (oid,name))

            if modules_to_delete:
                cr.execute("UPDATE ir_module_module SET state='uninstalled' WHERE id IN %s",(tuple(modules_to_delete.keys()),))
                cr.execute("DELETE FROM ir_model_constraint WHERE module in %s",(tuple(modules_to_delete.keys()),))
                cr.execute("DELETE FROM ir_model_relation WHERE module in %s",(tuple(modules_to_delete.keys()),))
                module_obj.unlink(cr,1,modules_to_delete.keys())

            models_to_delete = {}
            for model in model_obj.browse(cr,1,model_obj.search(cr,1,[])):
                if not registry.get(model.model):
                    models_to_delete[model.id]=model.model
            #
            for oid,name in models_to_delete.items():
                logger.info("Delete model [%s] %s" % (oid,name))

            if models_to_delete:
                cr.execute("DELETE FROM ir_rule WHERE model_id in %s",(tuple(models_to_delete.keys()),))
                cr.execute("DELETE FROM ir_model_constraint WHERE model in %s",(tuple(models_to_delete.keys()),))
                cr.execute("DELETE FROM ir_model_relation WHERE model in %s",(tuple(models_to_delete.keys()),))
                cr.execute("DELETE FROM ir_model WHERE id in %s",(tuple(models_to_delete.keys()),))

    #         model_data_obj = registry.get('ir.model.data')
    #         view_obj = registry.get('ir.ui.view')
    #         for model_data in model_data_obj.browse(cr,1,model_data_obj.search(cr,1,[])):
    #             obj = registry.get(model_data.model)
    #             if not obj:
    #                 logger.info("Delete ir_model_data [%s] %s " % (model_data.id,model_data.model))
    #                 model_data_obj.unlink(cr,1,[model_data.id])
    #             elif not obj.exists(cr, 1, model_data.res_id):
    #                 logger.info("Delete ir_model_data [%s] %s " % (model_data.id,model_data.model))
    #                 model_data_obj.unlink(cr,1,[model_data.id])
    #
    #         for view in view_obj.browse(cr,1,view_obj.search(cr,1,[])):
    #             xml_id = view.xml_id
    #             if xml_id:
    #                 view_modul = xml_id.split(".")[0]
    #                 if view_modul not in module_set and view_modul not in ("ir","res"):
    #                     logger.info("Delete ir_ui_view [%s] %s" % (view.id, xml_id))
    #                     view.unlink()

            cr.commit()
        except Exception, e:
            logger.error(e)
            return
        finally:
            cr.close()

    logger.info("finished!")

def add_parser(subparsers):
    parser = subparsers.add_parser('cleanup',
        description='Cleanup an existing OpenERP database')
    common2.add_common_server(parser)
    parser.set_defaults(run=run)
    parser.add_argument('--full', action='store_true', help='Full Cleanup (Update have to be done before)', required=False)
    parser.add_argument('--fix', action='store_true', help='Fix moved model data', required=False)
    parser.add_argument('--verbose', action='store_true', help='Fix moved model data', required=False)
