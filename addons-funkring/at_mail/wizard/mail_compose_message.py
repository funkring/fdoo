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
from openerp.addons.at_base.format import LangFormat
from openerp.addons.mail.wizard.mail_compose_message import EXPRESSION_PATTERN
from openerp import tools

class mail_compose_message(osv.TransientModel):
    
    def _get_render_env(self, cr, uid, template, model, res_ids, variables, context=None):
        variables = super(mail_compose_message, self)._get_render_env(cr, uid, template, model, res_ids, variables, context=context)
        langFormat = LangFormat(cr, uid, context=context)
        variables["formatLang"]=langFormat.formatLang
        return variables
    
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

    