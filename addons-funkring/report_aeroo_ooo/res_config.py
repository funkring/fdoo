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
from openerp import tools
from openerp.tools.translate import _

class aeroo_report_config(osv.osv_memory):
    _name = "aeroo.report.config"
    _description = "Aeroo Report Configuration"
    _inherit = "res.config.settings"
    _columns = {
        "host" : fields.char("Host",help="Default is localhost"),
        "port" : fields.integer("Port",help="Default is 8099"),
        "test_ok" : fields.boolean("Test OK", readonly=True)
    }
    
    def onchange_connection(self, cr, uid, ids, host, port, context=None):
        return { "value" : {"test_ok" : False} }
    
    def test_connection(self, cr, uid, ids, context=None):
        for config in self.browse(cr, uid, ids, context=context):
            report_obj = self.pool["ir.actions.report.xml"]
            try:
                with tools.file_open('report_aeroo_ooo/test_temp.odt', mode='rb') as fp:
                    file_data = fp.read()
                    with report_obj._new_ooproxy(cr, uid, host=config.host, port=config.port, context=context) as DC:
                        DC.putDocument(file_data)
                        DC.readDocumentFromStreamAndClose()
            except Exception, e:
                raise osv.except_osv(_("Error"), str(e))
            
        self.write(cr, uid, ids,  {"test_ok" : True}, context=context)
        return True
    
    def get_default_host(self, cr, uid, fields, context=None):
        return {"host":self.pool.get("ir.config_parameter").get_param(cr, uid, "ooproxy_host", default="127.0.0.1", context=context)}
        
    def get_default_port(self, cr, uid, fields, context=None):
        return {"port":int(self.pool.get("ir.config_parameter").get_param(cr, uid, "ooproxy_port", default="8099", context=context))}
        
    def set_default_host(self, cr, uid, ids, context=None):
        for config in self.browse(cr, uid, ids, context=context):
            self.pool.get("ir.config_parameter").set_param(cr, uid, "ooproxy_host", config.host, context=context)
            
    def set_default_port(self, cr, uid, ids, context=None):
        for config in self.browse(cr, uid, ids, context=context):
            self.pool.get("ir.config_parameter").set_param(cr, uid, "ooproxy_port", config.port, context=context)
            
    