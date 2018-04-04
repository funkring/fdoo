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

from openerp.addons.at_base import extreport, util

class Parser(extreport.basic_parser):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            "util" : util,
            "remind" : self._remind
        })
        
           
    def _get_currency(self, remind):
        return remind.profile_id.company_id.currency_id.symbol or ''
    
    def _eval_text(self,text,partner,profile,str_date):
        res = ""
        if text:
            val = {
                "partner_name": partner.name,
                "partner_salutation" : partner.mail_salutation or "",
                "date": self.formatLang(str_date,date=True),
                "company_name": profile.company_id.name,
                "user_signature": self.pool.get("res.users").browse(self.cr, self.uid, self.uid, self.localcontext).signature,
            }            
            res = text % val
        return res
    
    def _remind(self, remind):
        dunning_fee = 0.0
        amount = 0.0
        max_profile_line_id = remind.max_profile_line_id
        commercial_partner = remind.partner_id.commercial_partner_id
        invoice_obj = self.pool["account.invoice"]
        

        # get text        
        profile_line = remind.max_profile_line_id
        partner = remind.partner_id
        profile = remind.max_profile_line_id.profile_id
        dunning_date = remind.date
        
        text_before = self._eval_text(profile_line.description, partner, profile, dunning_date)
        text_after = self._eval_text(profile_line.description2, partner, profile, dunning_date)
        
        # calc lines
        lines = []
        for line in remind.line_ids:
            invoice = line.invoice_id
            amount+=invoice.residual
            lines.append({
              "amount" : invoice.residual,
              "inv" : invoice,
              "obj" : line      
            })
                          
            
        # calc refunds and out invoices
                
        inv_types = []
        if profile.ininvoices:
          inv_types.append("in_invoice")
        if not profile.norefund:
          inv_types.append("out_refund")
        
        invoices = []
        
        if inv_types:
          invoice_ids = invoice_obj.search(self.cr, self.uid, [("partner_id","=",commercial_partner.id),("state","=","open"),("type","in", inv_types)])          
          for invoice in invoice_obj.browse(self.cr, self.uid, invoice_ids, context=self.localcontext):
              if invoice.residual:
                  invoice_amount = 0.0
                  if invoice.type in ("out_refund","in_invoice"):
                      invoice_amount=-invoice.residual
                  else:
                      invoice_amount=invoice.residual
                  invoices.append({
                      "inv" : invoice,
                      "amount" : invoice_amount
                  })
                  amount += invoice_amount
                             
            
        if max_profile_line_id.dunning_fee_percent:
            dunning_fee = (amount / 100) * max_profile_line_id.dunning_fee
        else:
            dunning_fee = max_profile_line_id.dunning_fee
            
        return [{"total" : amount+dunning_fee,
                 "fee" : dunning_fee,
                 "amount" : amount,
                 "text_before" : text_before,
                 "text_after" : text_after,
                 "currency" : remind.profile_id.company_id.currency_id.symbol or '',
                 "invoices" : invoices,
                 "lines" : lines 
                }]
        
