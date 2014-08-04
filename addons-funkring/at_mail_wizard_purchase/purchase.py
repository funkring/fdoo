# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

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

from openerp.osv import osv
from openerp.tools.translate import _

class purchase_order_line(osv.osv):
    
    def mail_quote_request(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context):
            return {
                "name" : _("Send Quote Request"),
                "view_type" : "form",
                "view_mode" : "form",
                "res_model" : "at_mail_wizard.mail_wizard",
                "context" : { 
                    "report_name" : "purchase.quotation", 
                    "prepare_email" : "quotation",
                    "active_ids" : [line.order_id.id],
                    "active_model" : "purchase.order"
                 },
                "type" : "ir.actions.act_window",
                "key2" : "client_action_multi",
                "target" : "new",
                "nodestroy": True
            }    
    
    _inherit = "purchase.order.line"
purchase_order_line()