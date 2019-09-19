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

class email_template(osv.osv):

    def _get_render_env(self, cr, uid, template, model, res_ids, variables, context=None):
        variables = super(email_template, self)._get_render_env(cr, uid, template, model, res_ids, variables, context=context)
        langFormat = LangFormat(cr, uid, context=context)
        variables["formatLang"]=langFormat.formatLang
        return variables

    _inherit = "email.template"