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
import os

def get_lang_file(args):
    from openerp import tools
    lang =  hasattr(args,"lang") and args.lang or tools.config.defaultLang
    lang_msg = "language %s" % (lang,)
    lang_filename = lang.split("_")[0] + ".po"
    return (lang,lang_msg,lang_filename)

def run_import(args):
    import openerp
    import logging

    #init logger
    logger = logging.getLogger('translation-import')

    #set defaults
    common2.set_common_server(args)

    #load registry
    registry = openerp.modules.registry.RegistryManager.get(
        args.database, update_module=True)

    module_obj = registry.get('ir.module.module')
    cr = registry.cursor() # TODO context manager

    #define overwrite
    context = {'overwrite': args.overwrite }

    try:
        lang,lang_msg,lang_filename = get_lang_file(args)
        module_paths = common2.get_module_paths(args)

        for m,module_path in module_paths.items():
            lang_dir = os.path.join(module_path,"i18n")
            if os.path.exists(lang_dir):
                if module_obj.search(cr, 1, [("state", "=", "installed"),("name","=",m)]):
                    logger.info('Read translation file for %s to %s', lang_msg, lang_filename)
                    lang_file_path = os.path.join(lang_dir,lang_filename)
                    openerp.tools.trans_load(cr,lang_file_path,lang,context=context)

    finally:
        cr.close()


def run_export(args):
    import openerp
    import logging

    #init logger
    logger = logging.getLogger('translation-export')

    #set defaults
    common2.set_common_server(args)

    #load registry
    registry = openerp.modules.registry.RegistryManager.get(
        args.database, update_module=True)

    module_obj = registry.get('ir.module.module')
    cr = registry.cursor() # TODO context manager

    try:
        lang,lang_msg,lang_filename = get_lang_file(args)
        module_paths = common2.get_module_paths(args)

        for m,module_path in module_paths.items():
            lang_dir = os.path.join(module_path,"i18n")
            if not os.path.exists(lang_dir):
                os.mkdir(lang_dir)
            if module_obj.search(cr, 1, [("state", "=", "installed"),("name","=",m)]):
                lang_file = os.path.join(lang_dir,lang_filename)
                logger.info('Writing translation file for %s to %s', lang_msg, lang_file)
                buf = file(lang_file, "w")
                openerp.tools.trans_export(lang, [m], buf, "po", cr)
                buf.close()

        cr.commit()
    finally:
        cr.close()


def add_parser(subparsers):
    subsubparser = subparsers.add_parser('translation',
        description='Translations Management').add_subparsers()

    # Import Parser
    import_parser = subsubparser.add_parser('import',
        description='Import Translation')
    common2.add_common_server(import_parser)
    import_parser.add_argument('--lang', help='Language', required=False)
    import_parser.add_argument('--overwrite', action='store_true',
                                  help='Overwrite Translation', required=False)
    import_parser.set_defaults(run=run_import)

    # Export Parser
    export_parser = subsubparser.add_parser('export',
        description='Export Translation')
    common2.add_common_server(export_parser)
    export_parser.add_argument('--lang', help='Language', required=False)
    export_parser.set_defaults(run=run_export)
