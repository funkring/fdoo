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
from openerp.addons.at_base import util
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class account_btakeover(osv.osv):
    
    def copy_data(self, cr, uid, oid, default=None, context=None):                
        if not default:
            default = {}      
        btakeover = self.browse(cr, uid, oid)
        default.update({
            "state" : "draft",
            "name" : btakeover.name+_(" copy")
        })
        
        res = super(account_btakeover,self).copy_data(cr,uid,oid,default,context)
        return res
    
    def do_draft(self, cr, uid, ids, context):
        btakeover_line_obj = self.pool.get("account.btakeover.line")
        move_obj = self.pool.get("account.move")
        
        for record in self.browse(cr, uid, ids):
            for line in record.line_ids:

                btakeover_line_obj.write(cr, uid, line.id, {"state" : "draft"}, context)
                move_obj.button_cancel(cr, uid, [line.move_id.id], context=context)
                move_obj.unlink(cr, uid, [line.move_id.id], context=context)
            self.write(cr, uid, record.id, {"state" : "draft"})
            
        return True
    
    def do_assumption(self, cr, uid, ids, context=None):
        
        btakeover_line_obj = self.pool.get("account.btakeover.line")
        account_obj = self.pool.get("account.account")
        move_obj = self.pool.get("account.move")
        journal_obj = self.pool.get("account.journal")
        period_obj = self.pool.get("account.period")
        #currency_obj = self.pool.get("res.currency")
        #currency_id = currency_obj.search(cr, uid, [("symbol", "=", "€")])
        
        user = self.pool.get("res.users").browse(cr, uid, uid)
        for btakeover in self.browse(cr, uid, ids):
            for line in btakeover.line_ids:
                account_ids = account_obj.search(cr, uid, [("code", "=", line.code), ("company_id", "=", user.company_id.id)])
                account_id = account_ids and account_ids[0] or None
                if account_id:
                    balance = account_obj._compute_account(cr,uid,[account_id],date_till=btakeover.date,context=context)[account_id]
                    balance_is = float(balance["balance"])
                    balance_diff = balance_is - line.balance_nominal
                
                else:
                    raise osv.except_osv(_('Error'),_('There is no account for the entered code!'))
                name= str(journal_obj.create_sequence(cr, uid, {"name" : btakeover.journal_id.name,
                                                      "code" : btakeover.journal_id.code}, context))
                date = btakeover.date
                if not date:
                    date = util.currentDate()
                period = period_obj.search(cr, uid, [("date_start", "=", util.getFirstOfMonth(date))])
                account = account_obj.browse(cr, uid, account_id)
                values = {"name" : name,
                          "ref" : _("Balance Correction %s" % (btakeover.name)),
                          "period_id" : period[0],
                          "journal_id" : btakeover.journal_id.id,
                          "date" : date,
                          "amount" : line.balance_nominal,
                          "line_id" : [(0,0, {"name" : name,
                                             "account_id" : btakeover.account_id.id,
                                             "currency_id" : account.currency_id.id,
                                             "period_id" : period[0],
                                             "journal_id" : btakeover.journal_id.id,
                                             "debit" : balance_diff > 0.0 and balance_diff or 0.0,
                                             "credit" : balance_diff < 0.0 and (balance_diff * -1) or 0.0}),
                                             (0,0,{"name" : name,
                                             "account_id" : account_id,
                                             "currency_id" : account.currency_id.id,
                                             "period_id" : period[0],
                                             "journal_id" : btakeover.journal_id.id,
                                             "debit" : balance_diff < 0.0 and (balance_diff * -1) or 0.0,
                                             "credit" : balance_diff > 0.0 and balance_diff or 0.0})]}
                move_id = move_obj.create(cr, uid, values, context)
                
                btakeover_line_obj.write(cr, uid, line.id, {"state" : "assumed", "move_id" : move_id, "balance_is" : balance_is}, context)
            self.write(cr, uid, btakeover.id, {"state" : "assumed", "date" : date})
        return True
    
    _name = "account.btakeover"
    _columns = {
        "name" : fields.char("Name", size=64, required=True),
        "date" : fields.date("Date"),
        "journal_id" : fields.many2one("account.journal", "Journal", required=True, domain=[("type", "=", "general")]),
        "line_ids" : fields.one2many("account.btakeover.line", "btakeover_id", "Lines"),
        "state" : fields.selection([("draft", "Draft"), ("assumed", "Assumed")], "State", readonly=True),
        "account_id" : fields.many2one("account.account", "Account", required=True)
    }
    
    _defaults = {
        "date" : util.currentDate(),
        "state" : "draft",
    }

class account_btakeover_line(osv.osv):
    
    def copy_data(self, cr, uid, oid, default=None, context=None):                
        if not default:
            default = {}      
            
        default.update({
            "state" : "draft",
            "move_id" : None,
            "balance_is" : 0.0,
        })
        if not default.has_key("btakeover_id"):
            default["btakeover_id"]=None
        if not default.has_key("move_id"):
            default["move_id"]=None
        
        res = super(account_btakeover_line,self).copy_data(cr,uid,oid,default,context)
        return res
    
    def _balance_is(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids)
        account_obj = self.pool.get("account.account")
        btakeover_obj = self.pool.get("account.btakeover")
        
        user = self.pool.get("res.users").browse(cr, uid, uid)
        for line in self.browse(cr, uid, ids):
                account_ids = account_obj.search(cr, uid, [("code", "=", line.code), ("company_id", "=", user.company_id.id)])
                account_id = account_ids and account_ids[0] or None
                if account_id:
                    balance = account_obj._compute_account(cr,uid,[account_id],date_till=btakeover_obj.browse(cr, uid, line.btakeover_id).date,context=context)[account_id]
                    res[line.id] = balance["balance"]
                else:
                    res[line.id] = 0.0
                
        return res
    
    def onchange_balance_nominal(self, cr, uid, ids, balance_nominal, btakeover_id, code):
        
        res = {
            "value" : {}
        }
        account_obj = self.pool.get("account.account")
        user_obj = self.pool.get("res.users")
        
        account_ids = account_obj.search(cr, uid, [("code","=", code), ("company_id","=", user_obj.browse(cr, uid, uid).company_id.id)])
        if account_ids:
            account = account_obj.browse(cr, uid, account_ids[0])
            account_balance = account.balance
            res["value"]["balance_is"] = account_balance
            
        return res
    
    _name = "account.btakeover.line"
    _columns = {
        "btakeover_id" : fields.many2one("account.btakeover", "Takeover"),
        "code" : fields.char("Account Number", size=16, required=True),
        "name" : fields.char("Account Name", size=64, required=True),
        "balance_nominal" : fields.float("Balance nominal", digits_compute=dp.get_precision("Account")),
        "balance_is" : fields.function(_balance_is, type="float", string="Balance is", digits_compute=dp.get_precision("Account")),
        "move_id" : fields.many2one("account.move", "Move"),
        "state" : fields.selection([("draft", "Draft"), ("assumed", "Assumed")], "State", readonly=True)
    }
    
    _defaults = {
        "state" : "draft"
    }
