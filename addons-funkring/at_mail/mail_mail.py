# -*- coding: utf-8 -*-
#############################################################################
#
#    Copyright (c) 2018 sunhill technologies GmbH <office@sunhill-technologies.com>
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

class mail_mail(osv.Model):
    _inherit = "mail.mail"
    
    def send_get_email_dict(self, cr, uid, mail, partner=None, context=None):
        """Return a dictionary for specific email values, depending on a
        partner, or generic to the whole recipients given by mail.email_to.

            :param browse_record mail: mail.mail browse_record
            :param browse_record partner: specific recipient partner
        """
        body = self.send_get_mail_body(cr, uid, mail, partner=partner, context=context)
        body_alternative = tools.html2plaintext(tools.html_sanitize(body))
        res = {
            'body': body,
            'body_alternative': body_alternative,
            'subject': self.send_get_mail_subject(cr, uid, mail, partner=partner, context=context),
            'email_to': self.send_get_mail_to(cr, uid, mail, partner=partner, context=context),
        }
        return res
