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

class wizard_multi_charts_accounts(osv.osv_memory):
    
    def _create_bank_journals_from_o2m(self, cr, uid, obj_wizard, company_id, acc_template_ref, context=None):
        '''
        This function creates bank journals and its accounts for each line encoded in the field bank_accounts_id of the
        wizard.

        :param obj_wizard: the current wizard that generates the COA from the templates.
        :param company_id: the id of the company for which the wizard is running.
        :param acc_template_ref: the dictionary containing the mapping between the ids of account templates and the ids
            of the accounts that have been generated from them.
        :return: True
        '''
        obj_acc = self.pool.get('account.account')
        obj_journal = self.pool.get('account.journal')

        # Build a list with all the data to process
        journal_data = []
        if obj_wizard.bank_accounts_id:
            for acc in obj_wizard.bank_accounts_id:
                vals = {
                    'acc_name': acc.acc_name,
                    'account_type': acc.account_type,
                    'currency_id': acc.currency_id.id,
                }
                journal_data.append(vals)
        ref_acc_bank = obj_wizard.chart_template_id.bank_account_view_id
        if journal_data and not ref_acc_bank.code:
            raise osv.except_osv(_('Configuration Error!'), _('You have to set a code for the bank account defined on the selected chart of accounts.'))

        current_num = 1
        journal_code_def = { "cash" : ["KAS",0], "bank" : ["BNK",0]}
        
        for line in journal_data:
            # Seek the next available number for the account code
            account_ids = obj_acc.search(cr, uid, [('code', '=', line["acc_name"]), ('company_id', '=', company_id)])
            if not account_ids:
                raise osv.except_osv(_('Configuration Error!'), _('Account %s does not exist') % (line["acc_name"],))
            
            account = obj_acc.browse(cr,uid,account_ids[0])
            line["acc_name"] = account.name
            
            #create the bank journal
            vals_journal = self._prepare_bank_journal(cr, uid, line, current_num, account.id, company_id, context=context)
            
            #set journal code
            journal_code_format = journal_code_def.get(line["account_type"])                        
            if journal_code_format:
                journal_code = journal_code_format[0]
                if journal_code_format[1]:
                    journal_code = journal_code + str(journal_code_format[1])
                vals_journal["code"]=journal_code
                journal_code_format[1]=journal_code_format[1]+1
                
            obj_journal.create(cr, uid, vals_journal)
            current_num += 1
        return True
   
    def default_get(self, cr, uid, fields, context=None):
        res = super(wizard_multi_charts_accounts, self).default_get(cr, uid, fields, context=context)
        if "bank_accounts_id" in fields:
            res.update({'bank_accounts_id':  [{'acc_name': "3135",'account_type':'bank'},                    
                                              {'acc_name': "2700",'account_type':'cash'}]})
        return res
   
    _inherit = "wizard.multi.charts.accounts"


#class account_bank_accounts_wizard(osv.osv_memory):    
#    _inherit = "account.bank.accounts.wizard"
#    _columns = {
#        "acc_name" : fields.selection([("3115","Bank Austria"),
#                                       ("3120","Raiffeisen"),
#                                       ("3125","Volksbank"),
#                                       ("3130","Oberbank"),
#                                       ("3135","Sparkasse"),
#                                       ("3140","Volkskreditbank"),
#                                       ("3145","CA-Bankverein"),
#                                       ("3180","Sonstige"),
#                                       ("2700","Kassa")
#                                       ], "Account Name")
#    }
    