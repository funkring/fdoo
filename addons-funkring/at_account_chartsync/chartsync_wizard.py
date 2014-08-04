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
import netsvc

class account_chartsync_wizard(osv.osv_memory):
    
    def _get_default_chart(self,cr,uid,context=None):
        
        chart_obj = self.pool.get("account.chart.template")
        chart_ids = chart_obj.search(cr, uid, [])
        
        return chart_ids[0]
        
    
    def do_sync(self, cr, uid, ids, context=None):
        
        logger = netsvc.Logger()
        account_template_obj = self.pool.get("account.account.template")
        account_obj = self.pool.get("account.account")
        
        for wizard in self.browse(cr, uid, ids):
            chart = wizard.chart_template_id
            base_account_ids = account_obj.search(cr,uid, [("parent_id","=",False)])
            base_account_id = None
            try:
                base_account_id=base_account_ids[0]
            except:
                raise osv.except_osv(_('Error'), _('No base accounts available'))
            
            # iterate over all template accounts 
            # and create the accounts not found in account.account
            for account_template in account_template_obj.browse(cr, uid, account_template_obj.search(cr, uid, [("id", "child_of", chart.account_root_id.id),("id","!=",chart.account_root_id.id)])):
                account_ids = account_obj.search(cr, uid, [("company_id", "=", wizard.company_id.id), ("code", "=", account_template.code)])
                #create new account
                if not account_ids:
                    values = {
                           "code" : account_template.code,
                           "name" : account_template.name,
                           "type" : account_template.type,
                           "parent_id" : base_account_id,
                           "company_id" : wizard.company_id.id,
                           "user_type" : account_template.user_type.id
                    }
                    account_obj.create(cr,uid,values)
            
            # iterate over all template accounts
            # and update the existing
            for account_template in account_template_obj.browse(cr, uid, account_template_obj.search(cr, uid, [("id", "child_of", chart.account_root_id.id),("id","!=",chart.account_root_id.id)])):
                account_ids = account_obj.search(cr, uid, [("company_id", "=", wizard.company_id.id), ("code", "=", account_template.code)])
                if account_ids:
                    account = account_obj.browse(cr, uid, account_ids[0])
                    parent_id = base_account_id
                    if account_template.parent_id:
                        parent_ids = account_obj.search(cr, uid, [("company_id", "=", wizard.company_id.id), ("code", "=", account_template.parent_id.code)])
                        if parent_ids:
                            parent_id = parent_ids[0]
                    
                    values = {
                            "name" : account_template.name,
                            "type" : account_template.type,
                            "user_type" : account_template.user_type.id,
                            "parent_id" : parent_id
                        }
                    try:
                        account_obj.write(cr, uid, [account.id], values, context)
                    except Exception,e:
                        logger.notifyChannel("account.chartsync_wizard", netsvc.LOG_ERROR, str(e))
                        raise e
        return { "type" : "ir.actions.act_window_close" }
    
    _name = "account.chartsync_wizard"
    _description = "Synchronizing Accounts"
    
    _columns = {
        "company_id" : fields.many2one("res.company", "Company", required=True),
        "chart_template_id" : fields.many2one("account.chart.template", "Accountchart Template", required=True)
    }
    _defaults = {
        "company_id": lambda self,cr,uid,c: self.pool.get("res.company")._company_default_get(cr, uid, "account.analytic.line", context=c),
        "chart_template_id" : _get_default_chart
    }
    
account_chartsync_wizard()