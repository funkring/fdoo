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
from openerp.addons.at_base import util

class res_partner(osv.osv):

    _inherit = "res.partner"

    def _check_birthday(self, cr, uid):
        dt_current = util.strToDate(util.currentDate())
        date_search = "%%-%02d-%02d" % (dt_current.month,dt_current.day)
        template_xmlid = "partner_birthday_mail.email_partner_birthday"

        partner_ids = self.search(cr, uid, [("birthday","ilike",date_search)])
        template_obj = self.pool["email.template"]
        template_id = self.pool["ir.model.data"].xmlid_to_res_id(cr, uid, template_xmlid)
        if template_id:
            for partner in self.browse(cr, uid, partner_ids):
                template_obj.send_mail(cr, uid, template_id, partner.id, force_send=True)





