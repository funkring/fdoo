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


from openerp.addons.at_base import util
from openerp.report import report_sxw
from openerp.tools.translate import _

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            "accounts_get" : self._accounts_get,            
            "date_from_get" : self._date_from_get,
            "date_to_get" : self._date_to_get,
            "code_str" : self._code_str,
            "name_str" : self._name_str,
            "debit_str" : self._debit_str,
            "credit_str" : self._credit_str,
            "balance_str" : self._balance_str,
        })        
        self.localcontext["report_title"] = context.get("report_title",_("Balance list"))
        self.localcontext["date_from"]=context.get("date_from",util.getFirstOfMonth(util.currentDate()))
        self.localcontext["date_to"]=context.get("date_to",util.getEndOfMonth(util.currentDate()))
    
    def _accounts_get(self):
        account_ids = self.objects
        account_obj = self.pool.get("account.account")
        
        res = {"accounts" : []}
        
        for account in account_ids:
            res_value = {}
            
            res_value["code"] = account.code
            res_value["name"] = account.name
            
            res_value["debit_from"] = account_obj._compute_account(self.cr, self.uid, [account.id], date_till=self.localcontext["date_from"])[account.id]["debit"]
            res_value["credit_from"] = account_obj._compute_account(self.cr, self.uid, [account.id], date_till=self.localcontext["date_from"])[account.id]["credit"]
            res_value["balance_from"] = account_obj._compute_account(self.cr, self.uid, [account.id], date_till=self.localcontext["date_from"])[account.id]["balance"]
            
            res_value["debit_to"] = account_obj._compute_account(self.cr, self.uid, [account.id], date_till=self.localcontext["date_to"])[account.id]["debit"]
            res_value["credit_to"] = account_obj._compute_account(self.cr, self.uid, [account.id], date_till=self.localcontext["date_to"])[account.id]["credit"]
            res_value["balance_to"] = account_obj._compute_account(self.cr, self.uid, [account.id], date_till=self.localcontext["date_to"])[account.id]["balance"]
            
            res_value["currency"] = account.company_id.currency_id.symbol
            res["accounts"].append(res_value)
            
        return res
    
    def _date_from_get(self):
        return str(self.localcontext["date_from"])
    
    def _date_to_get(self):
        return str(self.localcontext["date_to"])
            
    def _code_str(self):
        return _("Code")
    
    def _name_str(self):
        return _("Name")
    
    def _debit_str(self):
        return _("Debit")
    
    def _credit_str(self):
        return _("Credit")
    
    def _balance_str(self):
        return _("Balance")
            
            