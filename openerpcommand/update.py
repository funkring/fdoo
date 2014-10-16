"""
Update an existing OpenERP database.
"""

from . import common2

def run(args):
    assert args.database
    import openerp

    #funkring begin
    import logging
    logger = logging.getLogger('update')
    common2.set_common_server(args)


    config = openerp.tools.config
    module = args.module
    if module:
        for m in module:
            config['update'][m] = 1
    else:
        config['update']['all'] = 1

    #try:
    openerp.modules.registry.RegistryManager.get(
        args.database, update_module=True)
    #except Exception,e:
    #    logger.error(e)
    #funkring end

def add_parser(subparsers):
    parser = subparsers.add_parser('update',
        description='Update an existing OpenERP database.')
    common2.add_common_server(parser)
    parser.set_defaults(run=run)
