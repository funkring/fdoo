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

from openerp.report import report_sxw
from openerp.tools.translate import _

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        
        invoice_fields = self.pool.get("account.invoice").fields_get(cr,uid,allfields=["state"])        
        self.localcontext.update({
            "last_payment" : self._last_payment,
            "date_str" : _("Date"),
            "number_str" : _("Invoice number"),
            "partner_str" : _("Partner"),
            "description_str" : _("Description"),
            "date_due_str" : _("Date due"),
            "residual_str" : _("Residual"),
            "amount_untaxed_str" : _("Amount untaxed"),
            "amount_total_str" : _("Amount total"),
            "state_str" : _("State"),
            "followup_str" :_("Reminder"),         
            "last_payment_str" : _("Payment"),
            "last_payment_journal_str" : _("Journal"),
            "reference_str" : _("Reference"),
            "taxes_str" : _("Taxes"),
            "state_dict" : dict(invoice_fields["state"]["selection"]),
            "short_name" : self._short_name,
            "accounts" : self._accounts,
        })        
        self.localcontext["report_title"] = context.get("report_title",_("Invoice overview"))        
        
    def _short_name(self,name):        
        if name:
            res = name.split(" ")
            return res[0]
        return None
    
    def _last_payment(self, invoice):
        res = {}
        payment_date = None
        payment_journal = None
        
        for payment in invoice.payment_ids:
            if not payment_date or payment_date < payment.date:
                payment_date = payment.date
                payment_journal = payment.journal_id.name
            
        res["payment_date"] = payment_date
        res["payment_journal"] = payment_journal
        
        return res
    
    def _accounts(self, invoice):
        res = []
        
        if invoice.move_id and invoice.move_id.line_id:
            for line in invoice.move_id.line_id:
                account = line.account_id
                if account:
                    value = {}
                    value["code"] = account.code
                    value["name"] = str(account.name[:16])
                    if len(account.name) > 16:
                        value["name"].strip()
                        value["name"]+=".."
                    res.append(value)
            
        return res