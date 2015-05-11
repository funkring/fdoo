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
import datetime

class res_partner(osv.osv):

    _inherit = "res.partner"

    def _send_mails(self, cr, uid, template_xmlid, ids, context=None):
        template_obj = self.pool["email.template"]
        template_id = self.pool["ir.model.data"].xmlid_to_res_id(cr, uid, template_xmlid)
        if template_id:
            today = datetime.date.today()
            for partner in self.browse(cr, uid, ids, context=context):
                birthday = partner.birthday
                if birthday.day == today.day and birthday.month == today.month:
                    template_obj.send_mail(cr, uid, template_id, partner.id, force_send=True, context=context)









