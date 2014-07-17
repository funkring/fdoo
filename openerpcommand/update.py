"""
Update an existing OpenERP database.
"""

#funkring.net begin
from . import common2
#funkring.net end
def run(args):
    assert args.database
    import openerp
    #funkring.net begin
    import logging
    logger = logging.getLogger('update')
    common2.set_common_server(args)
    #funkring.net end
    config = openerp.tools.config
    #funkrnig.net begin
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
    #funkrnig.net end

def add_parser(subparsers):
    parser = subparsers.add_parser('update',
        description='Update an existing OpenERP database.')
    #funkring.net begin
    common2.add_common_server(parser)
    #funkring.net end
    parser.set_defaults(run=run)
