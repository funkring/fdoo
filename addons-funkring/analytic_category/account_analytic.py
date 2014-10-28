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

from openerp.osv import fields, osv

UID_ROOT = 1

class account_analytic_account(osv.Model):
    _inherit = "account.analytic.account"
    _columns = {
        "category_id" : fields.many2one("account.analytic.category", "Category", ondelete="restrict")                
    }  

        
class account_analytic_category(osv.Model):
    _name = "account.analytic.category"
    _description = "Analytic Category"
    _columns = {
        "name" : fields.char("Name", required=True),        
        "code" : fields.char("Code")
    } 
    

class account_analytic_line(osv.Model):
    
    def _relids_analytic_account(self, cr, uid, account_ids, context=None):
        account_obj = self.pool["account.analytic.account"]
        all_account_ids = account_obj.search(cr, UID_ROOT, [("id","child_of",account_ids)], context=context)
        cr.execute("SELECT l.id FROM account_analytic_line l "
                   " WHERE l.account_id IN %s", (tuple(all_account_ids),))
        res = [r[0] for r in cr.fetchall()]
        return res
    
    def _category_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for line in self.browse(cr, uid, ids, context):
            # get account
            account = line.account_id
            # if account has no category, check parents
            while account and not account.category_id:
                account = account.parent_id
            if account.category_id:
                res[line.id]=account.category_id.id
        return res
    
    _inherit = "account.analytic.line"
    _columns = {
        "category_id" : fields.function(_category_id, string="Category", type="many2one", relation="account.analytic.category", store={
            "account.analytic.account" : (_relids_analytic_account,["parent_id","category_id"],10),
            "account.analytic.line": (lambda self, cr, uid, ids, context=None: ids, ["account_id"],10)
        })
    }
