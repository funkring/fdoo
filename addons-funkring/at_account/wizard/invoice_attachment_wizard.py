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

import base64

from openerp.addons.report_aeroo import report_aeroo
from openerp.addons.at_base import util
from openerp.osv import fields, osv
from openerp.tools.translate import _

class inovice_attachment_wizard(osv.TransientModel):
    _name = "account.invoice.attachment.wizard"
    _description = "Invoice Attachment Wizard"
    
    def action_import(self, cr, uid, ids, context=None):
        wizard =  self.browse(cr, uid, ids[0])
        invoice_id =  util.active_id(context, "account.invoice")
        if not invoice_id:
            raise osv.except_osv(_("Error!"), _("No invoice found"))
        report_obj = self.pool.get("ir.actions.report.xml")
        
        data=base64.decodestring(wizard.document)
        data = report_aeroo.fixPdf(data)
        if not data:
            raise osv.except_osv(_("Error!"), _("PDF is corrupted and unable to fix!"))
        
        if not report_obj.write_attachment(cr, uid, "account.invoice", invoice_id, datas=base64.encodestring(data), context=context, origin="account.invoice.attachment.wizard"):
            raise osv.except_osv(_("Error!"), _("Unable to import document (check if invoice is validated)"))          
        return { "type" : "ir.actions.act_window_close" }
    
    _columns = {
        "document" : fields.binary("Document")
    }