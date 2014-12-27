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

class assign_registration_wizard(models.TransientModel):
    
    @api.one
    def action_assign(self):
        reg_obj = self.env["academy.registration"]
        reg_ids = util.active_ids(self._context,reg_obj)
        regs = reg_obj.search([("id","in",reg_ids),("state","=","registered")])
        if regs:
            regs.action_assign()
        return {'type': 'ir.actions.act_window_close'}
    
    _name = "academy.assign.registration.wizard"
    _description = "Assign"

    
