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

class mail_compose_message(osv.Model):
    
    def _res_ids(self, wizard, context=None):
        mass_mode = wizard.composition_mode in ('mass_mail', 'mass_post')
        if mass_mode and wizard.use_active_domain and wizard.model:
            res_ids = self.pool[wizard.model].search(cr, uid, eval(wizard.active_domain), context=context)
        elif mass_mode and wizard.model and context.get('active_ids'):
            res_ids = context['active_ids']
        else:
            res_ids = [wizard.res_id]
        return res_ids
    
    _inherit = "mail.compose.message"

    