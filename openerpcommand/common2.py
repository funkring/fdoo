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

import os
from common import set_addons
from common import add_addons_argument
from common import required_or_default


def add_common_server(parser):
    """
    Parse server commons:
      database, module
    """
    add_addons_argument(parser)
    parser.add_argument('--database', metavar='DATABASE',
        **required_or_default('DATABASE',
                              'the database to modify'))    
    parser.add_argument('-m', '--module', metavar='MODULE', required=False)
    parser.add_argument('--default-lang',required=False)
    
    
def set_common_server(args):
    """
      Turn args.module into a list,
      call set_addons,
      initialize logger
    """
    import openerp
    from openerp.tools import config 
        
    set_addons(args)
    
    if hasattr(args,'module'):
        args.module = args.module and args.module.split(',') or None
    
    if hasattr(args,'default_lang'):
        if args.default_lang:
            if len(args.default_lang) > 5:
                raise Exception('ERROR: The Lang name must take max 5 chars, Eg: -lde_DE')
            config.defaultLang = args.default_lang            
            
    openerp.netsvc.init_logger()
    
def get_module_paths(args):
    """
    Build a map with module to module Paths
    """
    res = {}
    if args.module:
        for m in args.module:        
            for addon_path in args.addons:            
                module_path = os.path.join(addon_path,m)
                if os.path.exists(module_path):
                    if not m in res:
                        res[m]=module_path
    return res
                
            