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

from openerp import models, fields, api, _

class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    @api.multi
    def invoice_send(self, force=False):
      # get template
      template = self.env.ref('account.email_template_edi_invoice', False)
      message_obj = self.env["mail.compose.message"]
      # send all unsent
      for inv in self:
        if not inv.sent or force:
          message = message_obj.with_context(
            default_template_id=template.id,                                        
            default_model="account.invoice",
            default_res_id=inv.id,
            mark_invoice_as_sent=True,
            default_partner_ids=[inv.partner_id.id],
            default_composition_mode="comment",
            default_notify=True).create({})
          # finally sent
          message.send_mail()
          
    @api.model
    def send_all_draft(self):
      for invoice in self.search([("state","=","draft")]):
        invoice.signal_workflow('invoice_open')
        invoice.invoice_send()
      return True
      
    
class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    
    @api.multi
    def _line_format(self):
        res = dict.fromkeys(self.ids, "")
        for line in self:
            if not line.product_id and not line.price_unit and not line.quantity:
                res[line.id] = "s"
        return res
    
    @api.model
    def move_line_get(self, invoice_id):
        inv = self.env['account.invoice'].browse(invoice_id)
        currency = inv.currency_id.with_context(date=inv.date_invoice)
        company_currency = inv.company_id.currency_id

        res = []
        for line in inv.invoice_line:
            mres = self.move_line_get_item(line)
            mres['invl_id'] = line.id
            res.append(mres)
            tax_code_found = False
            taxes = line.invoice_line_tax_id.compute_all(
                (line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)),
                line.quantity, line.product_id, inv.partner_id)['taxes']
            for tax in taxes:
                # funkring.net  - begin    
                if inv.type in ('out_invoice', 'in_invoice'):
                    if inv.type == "in_invoice":
                        tax_code_id = tax['ref_base_code_id']
                    else:
                        tax_code_id = tax['base_code_id']
                    tax_amount = tax['price_unit'] * line.quantity * tax['base_sign']
                else:
                    if inv.type == "in_refund":
                        tax_code_id = tax['base_code_id']
                    else:
                        tax_code_id = tax['ref_base_code_id']
                    tax_amount = tax['price_unit'] * line.quantity * tax['ref_base_sign']
                # funkring.ent - end

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(dict(mres))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = currency.compute(tax_amount, company_currency)

        return res