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
            "get_sum" : self._get_sum,
            "get_currency" : self._get_currency,
            "get_dunning_fee" : self._get_dunning_fee,
            "reminder_text" : self._reminder_text
        })
        
           
    def _get_sum(self, reminder):
        res = 0.0
        for line in reminder.line_ids:
            invoice = line.invoice_id
            res+=invoice.residual
        return res
    
    def _get_currency(self, remind):
        return remind.profile_id.company_id.currency_id.symbol or ''
    
    def _get_dunning_fee(self, reminder):
        dunning_fee = 0.0
        amount = 0.0
        max_profile_line_id = reminder.max_profile_line_id
        for line in reminder.line_ids:
            invoice = line.invoice_id
            amount+=invoice.residual
        if max_profile_line_id.dunning_fee_percent:
            dunning_fee = (amount / 100) * max_profile_line_id.dunning_fee
        else:
            dunning_fee = max_profile_line_id.dunning_fee
            
        return dunning_fee
    
    def _reminder_text(self, reminder):
        profile_line = reminder.max_profile_line_id
        partner = reminder.partner_id
        profile = reminder.max_profile_line_id.profile_id
        dunning_date = reminder.date
        
        text_before = self._eval_text(profile_line.description, partner, profile, dunning_date)
        text_after = self._eval_text(profile_line.description2, partner, profile, dunning_date)
        
        return {"text_before" : text_before,
                "text_after" : text_after}
        
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
