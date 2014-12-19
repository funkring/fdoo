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

from openerp import models, fields, api, _
from openerp.addons.at_base import util

class validate_log_wizard(models.TransientModel):
    
    @api.one
    def action_validate(self):
        log_obj = self.env["farm.chicken.log"]
        log_ids = util.active_ids(self._context,log_obj)
        logs = log_obj.search([("id","in",log_ids),("state","=","draft")])
        if logs:
            logs.action_validate()
        return {'type': 'ir.actions.act_window_close'}
    
    _name = "farm.chicken.validate.log.wizard"
    _description = "Validate Logs"
