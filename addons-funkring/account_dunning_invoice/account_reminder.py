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

from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp.exceptions import Warning

class account_reminder(osv.Model):
         
    def send_reminder_mail(self, cr, uid, ids, context=None):
      res = super(account_reminder, self).send_reminder_mail(cr, uid, ids, context=context)
      report_obj = self.pool["ir.actions.report.xml"]
      if len(ids) > 1: 
        return res
      
      report_obj = self.pool["ir.actions.report.xml"]
      att_ids = []
      
      report_name = "account.report_invoice"
      report = report_obj._lookup_report(cr, report_name)
      report_ctx = context and dict(context) or {}
      
      for reminder in self.browse(cr, uid, ids, context=context):
        for line in reminder.line_ids:
          invoice = line.invoice_id
          report.create(cr, uid, [invoice.id], {"model":"account.invoice"}, report_ctx)
                  
          att_id = report_obj.get_attachment_id(cr, uid, "account.invoice", invoice.id, report_name, context=context)
          if att_id:
            att_ids.append(att_id)
      
      if att_ids:
        res["context"]["attachment_ids"] = att_ids
        
      return res
   
    _inherit = "account.reminder"

 