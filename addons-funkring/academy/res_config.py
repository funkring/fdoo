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

class academy_config_settings(osv.TransientModel):
    _name = "academy.config.settings"
    _inherit = "res.config.settings"
    _columns = {
        "webuser_id" : fields.many2one("res.users","Academy Web User", required=True)
    }
    
    def get_default_webuser_id(self, cr, uid, fields, context=None):
        user = self.pool["res.users"].browse(cr, uid, uid, context=context)
        return { "webuser_id" : user.company_id.academy_webuser_id.id or uid }
    
    def set_webuser_id(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool["res.users"].browse(cr, uid, uid, context)
        user.company_id.write({"academy_webuser_id" : config.webuser_id.id })
        
                             