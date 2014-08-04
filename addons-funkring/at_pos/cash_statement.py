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

class account_cash_statement(osv.osv):

    def _pos_paid_order_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)        
        for oid in ids:
            res[oid]=[]
        
        cr.execute("SELECT o.statement_id, o.id FROM pos_order o WHERE "  
                   " o.state IN ('done','paid') AND o.statement_id IN %s ",(tuple(ids),))
                
        for row in cr.fetchall():
            order_list = res.get(row[0])                 
            order_list.append(row[1])            
        return res
        
        
    def _pos_paid_order_line_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)        
        for oid in ids:
            res[oid]=[]
                
        cr.execute("SELECT o.statement_id, l.id FROM pos_order o "
                   " INNER JOIN pos_order_line l ON l.order_id = o.id "  
                   " WHERE o.state IN ('done','paid') AND o.statement_id IN %s "
                   ,(tuple(ids),))
        
        for row in cr.fetchall():
            order_list = res.get(row[0])                 
            order_list.append(row[1])            
        return res
    
    def button_open(self, cr, uid, ids, context=None):
        for stmt in self.browse(cr, uid, ids, context):
            if stmt.journal_id.parent_id and (not stmt.parent_id or stmt.parent_id.journal_id.id != stmt.journal_id.parent_id.id):
                raise osv.except_osv(_("Error"), _("Statment must have an parent statement from journal %s") % ( stmt.journal_id.parent_id.name,))        
        res = super(account_cash_statement,self).button_open(cr,uid,ids,context=context)
        return res
    
    def button_confirm_cash(self, cr, uid, ids, context=None):
        #
        for stmt in self.browse(cr,uid,ids,context=context):
            for child in stmt.child_ids:                
                self.write(cr, uid, [child.id], {"period_id" : stmt.period_id.id }, context=context)
                self.button_confirm_cash(cr,uid,[child.id],context=context)
        #
        res = super(account_cash_statement, self).button_confirm_cash(cr, uid, ids, context=context)
        cr.execute("SELECT p.id FROM account_bank_statement_line l "
                   " INNER JOIN pos_order p ON p.id = l.pos_statement_id AND p.state = 'paid' "
                   " WHERE l.statement_id IN %s "
                   " GROUP BY 1", (tuple(ids),))
        
        order_obj = self.pool.get("pos.order")
        wf_service = netsvc.LocalService("workflow")
        
        order_ids = [r[0] for r in cr.fetchall()]
        for order in order_obj.browse(cr, uid, order_ids, context=context):
            todo = True
            for line in order.statement_ids:
                if line.statement_id.state <> 'confirm':
                    todo = False
                    break
            if todo:
                wf_service.trg_validate(uid, 'pos.order', order.id, 'done', cr)
        return res
    
    def create_move_from_st_line(self, cr, uid, st_line_id, company_currency_id, next_number, context=None):
        res = super(account_cash_statement, self).create_move_from_st_line(cr, uid, st_line_id, company_currency_id, next_number, context=context)
        #
        bank_st_line_obj = self.pool.get("account.bank.statement.line")        
        st_line = bank_st_line_obj.browse(cr, uid, st_line_id, context=context)                
        stmt = st_line.statement_id
        partner = st_line.partner_id
        #
        amount = st_line.amount        
        #
        if amount > 0 and stmt.journal_id.balance_credit and partner:                
            account_move_obj = self.pool.get("account.move")       
            account_move_line_obj = self.pool.get("account.move.line")
            receivable_account = partner.property_account_receivable
            
            seq = 1                
            #               
            cr.execute("SELECT l.id FROM account_move_line l "                        
                       " WHERE l.credit > 0 AND reconcile_id IS NULL AND l.account_id = %s ", (receivable_account.id,) )
            #
            refund_move_line_ids = [r[0] for r in cr.fetchall()]
            for refund_move_line in account_move_line_obj.browse(cr,uid,refund_move_line_ids,context=context):
                residual = refund_move_line.amount_residual
                reconcile_move_ids = []
                if residual > 0:
                    move_id = account_move_obj.create(cr, uid, {
                                "journal_id" : stmt.journal_id.id,
                                "period_id" : stmt.period_id.id,
                                "date" : stmt.date,
                                "name" : "%s/%d" % (next_number,seq)
                              }, context=context)
                    
                    balance = min(amount,residual)
                    bank_st_line_obj.write(cr, uid, [st_line_id], {"move_ids" : [(4, move_id, False)]})
                    
                    debit_move_line_id = account_move_line_obj.create(cr,uid,  {
                            "name" : st_line.name,
                            "date" : st_line.date,                                
                            "ref" : st_line.ref,
                            "move_id" : move_id,
                            "partner_id" : partner.id,
                            "account_id" : receivable_account.id,
                            "credit" : 0.0,
                            "debit" :  balance,
                            "statement_id" : stmt.id,
                            "journal_id" : stmt.journal_id.id,
                            "period_id" : stmt.period_id.id,
                            "currency_id" : stmt.currency.id,
                            "analytic_account_id" : st_line.analytic_account_id and st_line.analytic_account_id.id or False
                        }, context=context)
                    
                    reconcile_move_ids.append(debit_move_line_id)
                    reconcile_move_ids.append(refund_move_line.id)
                                                                  
                    account_move_line_obj.create(cr,uid,  {
                            "name" : st_line.name,
                            "date" : st_line.date,                                
                            "ref" : st_line.ref,
                            "move_id" : move_id,
                            "partner_id" : partner.id,
                            "account_id" : stmt.journal_id.default_credit_account_id.id,
                            "credit" : balance,
                            "debit" :  0.0,
                            "statement_id" : stmt.id,
                            "journal_id" : stmt.journal_id.id,
                            "period_id" : stmt.period_id.id,
                            "currency_id" : stmt.currency.id,
                            "analytic_account_id" : st_line.analytic_account_id and st_line.analytic_account_id.id or False
                        }, context=context)
                    
                    account_move_obj.post(cr,uid,[move_id],context=context)
                    
                    if refund_move_line.reconcile_partial_id:
                        reconcile_move_ids.extend([m.id for m in refund_move_line.reconcile_partial_id.line_partial_ids])
                                 
                    account_move_line_obj.reconcile_partial(cr, uid, reconcile_move_ids, context=context)
                    
                    amount-=balance
                    if amount<=0.0:
                        break
                    seq+=1            
        return res

                
    _inherit = 'account.bank.statement'    
    _columns = {
        "pos_paid_order_line_ids" : fields.function(_pos_paid_order_line_ids,string="Paid Order Lines", type="many2many",relation="pos.order.line"),
        "pos_paid_order_ids" : fields.function(_pos_paid_order_ids,string="Paid Orders", type="many2many",relation="pos.order"),        
        "parent_id" : fields.many2one("account.bank.statement", "Parent",readonly=True, states={'draft':[('readonly',False)]},select=True),
        "child_ids" : fields.one2many("account.bank.statement", "parent_id", string="Children", readonly=True, states={'draft':[('readonly',False)]}, select=True)
    }
    
account_cash_statement()
