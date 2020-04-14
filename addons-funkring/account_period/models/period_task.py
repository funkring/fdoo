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

from collections import OrderedDict

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp


class AccountPeriodTask(models.Model):
    _name = "account.period.task"
    _description = "Period Processing"
    _inherit = ["mail.thread", "util.time", "util.report"]
    _inherits = {"automation.task": "task_id"}
    
    _order = "id desc"
    _sum_fields = ("amount_gross",
                   "amount_net",
                   "amount_tax",
                   "payment_amount",
                   "private_amount")
    
    @api.model
    def _default_company(self):
        return self.env['res.company']._company_default_get("account.period.task")
    
    @api.model
    def _default_period(self):
        period_start = self._firstOfLastMonth()
        period_obj = self.env["account.period"]
        
        period = period_obj.search([("date_start","=",period_start)], limit=1)
        if not period:
            period = period_obj.search([], limit=1, order="date_start desc")
        
        return period
    
    @api.onchange("period_id", "company_id")
    def _onchange_period_profile(self):
        name = "/"
        if self.period_id:
            name = self.period_id.name
        self.name = name

    task_id = fields.Many2one(
        "automation.task", "Task", required=True, index=True, ondelete="cascade"
    )
    
    period_id = fields.Many2one("account.period", "Period", required=True,
                                ondelete="restrict",
                                default=_default_period,
                                readonly=True, states={'draft': [('readonly', False)]})
    
    company_id = fields.Many2one("res.company", "Company", 
        ondelete="restrict", required=True, default=_default_company,
        readonly=True, states={'draft': [('readonly', False)]}
    )
    
    
    entry_count = fields.Integer("Entries", compute="_compute_entry_count", 
                                 store=False, readonly=True)
    
    entry_ids = fields.One2many("account.period.entry", "task_id", "Entries", 
                                readonly=True)
    
    tax_ids = fields.One2many("account.period.tax", "task_id", "Taxes",
                                readonly=True)
    
    tax_total = fields.Float("Total Tax", digits=dp.get_precision("Account"),
                             readonly=True)
    
    currency_id = fields.Many2one("res.currency", "Currency", relation="company_id.currency_id", readonly=True)
    
    
    @api.multi
    def _compute_entry_count(self):
        for task in self:
            self.entry_count = len(task.entry_ids)
    
    @api.multi
    def entry_action(self):
        for task in self:
            return {
                "display_name" : _("Entries"),
                "view_type" : "form",
                "view_mode" : "tree,form",
                "res_model" : "account.period.entry",
                "domain": [("task_id","=",task.id)],          
                "type" : "ir.actions.act_window",
            }
            
    @api.multi
    def tax_action(self):
        for task in self:
            return {
                "display_name" : _("Taxes"),
                "view_type" : "form",
                "view_mode" : "tree,form",
                "res_model" : "account.period.tax",
                "domain": [("task_id","=",task.id)],          
                "type" : "ir.actions.act_window",
            }
            
    
    @api.model
    @api.returns("self", lambda self: self.id)
    def create(self, vals):
        res = super(AccountPeriodTask, self).create(vals)
        res.res_model = self._name
        res.res_id = res.id
        return res

    @api.multi
    def action_queue(self):
        return self.task_id.action_queue()

    @api.multi
    def action_cancel(self):
        return self.task_id.action_cancel()

    @api.multi
    def action_refresh(self):
        return self.task_id.action_refresh()

    @api.multi
    def action_reset(self):
        return self.task_id.action_reset()

    @api.multi
    def unlink(self):
        cr = self._cr
        ids = self.ids
        cr.execute(
            "SELECT task_id FROM %s WHERE id IN %%s AND task_id IS NOT NULL"
            % self._table,
            (tuple(ids),),
        )
        task_ids = [r[0] for r in cr.fetchall()]
        res = super(AccountPeriodTask, self).unlink()
        self.env["automation.task"].browse(task_ids).unlink()
        return res

    def _run_options(self):
        return {"stages": 1, "singleton": True}

    def _create_payment_based(self, taskc, journals):
        """ search for invoices and receipts, which are in 
            the passed journal, and paid in this period """
        
        journal_ids = tuple(journals.ids)
        period = self.period_id
        period_start = period.date_start
        period_end = period.date_stop
        
        taskc.logd("create payment based")
        
        def getTaxId(taxes):
            taxes = taxes["taxes"]
            if not taxes:
                return None
            return taxes[0]["id"]
        
        moves = OrderedDict()        
        def addMove(values):
            move_id = values["move_id"]
            journal_id = values["journal_id"]                        
            account_id = values["account_id"]
            invoice_id = values.get("invoice_id", None)
            voucher_id = values.get("voucher_id", None)
            tax_id = values.get("tax_id", None)
                        
            key = (move_id, journal_id, account_id, invoice_id, voucher_id, tax_id)
            move_data = moves.get(key, None)
            if move_data is None:
                move_data = dict(values)
                move_data["task_id"] = self.id
                
                for field in self._sum_fields:
                    move_data[field] = values.get(field, 0.0)
                    
                moves[key] = move_data
            else:
                # sumup fields
                for field in self._sum_fields:
                    move_data[field] += values.get(field, 0.0)
            
            move_data["amount_tax"] = move_data["amount_gross"] - move_data["amount_net"]
        
        cr = self.env.cr
        
        #######################################################################
        # search for invoice which has a payment 
        # paid in this period
        # evaluate product an calculate 
        # ... private usage
        # ... reverse charge, IGE (service or product)
        # ... incoming vat 
        #######################################################################
            
        taskc.substage("Invoice Tax")
               
        # search for reconciled 
                
        cr.execute("""SELECT
            i.id
        FROM account_move_reconcile r
        INNER JOIN account_move_line l ON (l.reconcile_id = r.id OR l.reconcile_partial_id = r.id)
        INNER JOIN account_invoice i ON i.move_id = l.move_id
        INNER JOIN account_move_line l2 on (l2.move_id != i.move_id AND (l2.reconcile_id = r.id OR l2.reconcile_id = r.id))        
        WHERE l2.date >= %(period_start)s 
          AND l2.date <= %(period_end)s
          AND i.journal_id IN %(journal_ids)s          
        GROUP BY 1
        """, {
            "period_start": period_start,
            "period_end": period_end,
            "journal_ids": journal_ids   
        })
        
        invoice_ids = [r[0] for r in cr.fetchall()]
        taskc.initLoop(len(invoice_ids), status="calc invoice tax")        
        for invoice in self.env["account.invoice"].browse(invoice_ids):
            taskc.nextLoop()
            
            if not invoice.amount_total:
                taskc.logw("Invoice is zero", ref="account.invoice,%s" % invoice.id)
                continue
            
            sign = 1.0
            if invoice.type in ("out_refund", "in_invoice"):
                sign = -1.0
            
            amount_paid = 0.0
            payment_date = None
            
            for move_line in invoice.payment_ids:
                if move_line.date >= period_start and move_line.date <= period_end:
                    amount_paid += (move_line.credit - move_line.debit)
                    payment_date = max(payment_date, move_line.date)
             
            if amount_paid:
                if invoice.state == "paid":
                    payment_state = "paid"
                    payment_rate = 1.0     
                elif amount_paid > 0.0:
                    payment_state = "part"
                    payment_rate = (1 / invoice.amount_total) * amount_paid
                else:
                    payment_state = "open"
                    payment_rate = 0.0
                    
                for line in invoice.invoice_line:
                    price = (line.price_unit * (1 - (line.discount or 0.0) / 100.0))
                    taxes = line.invoice_line_tax_id.compute_all(price, line.quantity, line.product_id, invoice.partner_id)
                    
                    
                    # generated amounts
                    # and multiplicate with payment rate factor
                    # to get really paid part
                    amount = price * line.quantity * payment_rate            
                    amount_gross = taxes["total_included"] * payment_rate
                    amount_net = taxes["total"] * payment_rate
                    
                    tax_id = getTaxId(taxes)
                    
                    account = line.account_id
                    if account.private_usage > 0:
                        private_amount = amount * account.private_usage
                    else:
                        private_amount = 0.0
                        
                    addMove({
                        "date": payment_date,
                        "move_id": invoice.move_id.id,
                        "journal_id": invoice.journal_id.id,
                        "account_id": account.id,
                        "invoice_id": invoice.id,                    
                        "tax_id": tax_id,
                        "amount": amount*sign,
                        "amount_gross": amount_gross*sign,
                        "amount_net": amount_net*sign,
                        "private_amount": private_amount*sign,
                        "payment_rate": payment_rate,
                        "payment_amount": amount_gross,
                        "payment_state": payment_state,
                        "payment_date": payment_date
                    })
                
        taskc.done()
        
        
        #######################################################################
        # search for receipts,
        # paid in this period which not belongs to invoices
        #######################################################################
        
        taskc.substage("Receipt Tax")
        
        cr.execute("""SELECT voucher_id, ARRAY_AGG(move_line_id) FROM
            (SELECT
                v.id AS voucher_id, l2.id AS move_line_id
            FROM account_move_reconcile r
            INNER JOIN account_move_line l ON (l.reconcile_id = r.id OR l.reconcile_partial_id = r.id)
            INNER JOIN account_voucher v ON v.move_id = l.move_id
            INNER JOIN account_move_line l2 on (l2.move_id != v.move_id AND (l2.reconcile_id = r.id OR l2.reconcile_id = r.id))            
            WHERE v.type IN ('sale','purchase')
            GROUP BY 1,2) t
        GROUP BY 1""", {
            "period_start": period_start,
            "period_end": period_end,
            "journal_ids": journal_ids   
        })
        
        res = cr.fetchall()
        voucher_ids = [r[0] for r in res]
        voucher_payment_line_ids = dict((r[0], r[1]) for r in res)
        
        move_line_obj = self.env["account.move.line"]
        taskc.initLoop(len(voucher_ids), status="calc receipt tax")    
        for voucher in self.env["account.voucher"].browse(voucher_ids):      
            taskc.nextLoop()
            
            sign = 1.0
            if invoice.type == "purchase":
                sign = -1.0
                  
            amount_paid = 0.0
            payment_date = None
                    
            move_line_ids = voucher_payment_line_ids.get(voucher.id)
            if not move_line_ids:
                continue
            
            for move_line in move_line_obj.browse(move_line_ids):
                if move_line.date >= period_start and move_line.date <= period_end:
                    amount_paid += (move_line.credit - move_line.debit)
                    payment_date = max(payment_date, move_line.date)
                        
            if amount_paid:             
                if voucher.paid:
                    payment_state = "paid"
                    payment_rate = 1.0     
                elif amount_paid > 0.0:
                    payment_state = "part"
                    payment_rate = (1 / voucher.amount) * amount_paid
                else:
                    payment_state = "open"
                    payment_rate = 0.0
                    
                taxes = voucher.tax_id.compute_all(amount, 1, product=None, 
                                                   partner=voucher.partner_id)
                tax_id = getTaxId(taxes)
                for line in voucher.line_ids:
                    # generated amounts
                    # and multiplicate with payment rate factor
                    # to get really paid part                
                    amount = line.amount * payment_rate            
                    amount_gross = taxes["total_included"] * payment_rate
                    amount_net = taxes["total"] * payment_rate
                    
                    account = line.account_id
                    if account.private_usage > 0:
                        private_amount = amount * account.private_usage
                    else:
                        private_amount = 0.0
                    
                    addMove({
                        "date": payment_date,
                        "move_id": voucher.move_id.id,
                        "journal_id": voucher.journal_id.id,
                        "account_id": account.id,
                        "invoice_id": None,                   
                        "tax_id": tax_id,
                        "amount": amount*sign,
                        "amount_gross": amount_gross*sign,
                        "amount_net": amount_net*sign,
                        "private_amount": private_amount*sign,
                        "payment_rate": payment_rate,
                        "payment_amount": amount_gross,
                        "payment_state": payment_state,
                        "payment_date": payment_date
                    })
                    
        taskc.done()
        
        #######################################################################
        # create moves
        #######################################################################
        
        entry_obj = self.env["account.period.entry"]
        taskc.substage("Create Entries")
        taskc.initLoop(len(moves), status="create entries")
        for entry_values in moves.itervalues():
            taskc.nextLoop()
            domain = [(f,"=",v) for (f,v) in entry_values.iteritems()]
            entry = entry_obj.search(domain)
            if not entry:
                entry = entry_obj.create(entry_values)
                
        taskc.done()
            
    def _create_tax(self, taskc):
        taskc.logd("create tax")
        
        cr = self._cr        
        tax_code_obj = self.env["account.tax.code"]
        period_tax_obj = self.env["account.period.tax"]
        
        taskc.substage("Create Tax")
        
        def calcTax(tax_code, parent_id=None):
            amount_base = 0.0
            amount_tax = 0.0
            
            # base for taxes to pay
            cr.execute("""SELECT 
                COALESCE(SUM(amount_net),0.0)
            FROM account_period_entry e
            INNER JOIN account_tax t ON t.id = e.tax_id
            INNER JOIN account_tax_code tc ON tc.id = t.base_code_id
            WHERE e.task_id = %s
              AND tc.id = %s
              AND amount_net > 0
            """, (self.id, tax_code.id))
            
            for (amount_base_entries,) in cr.fetchall():
                amount_base += amount_base_entries
            
            # base for taxes refund
            cr.execute("""SELECT 
                COALESCE(SUM(amount_net),0.0)
            FROM account_period_entry e
            INNER JOIN account_tax t ON t.id = e.tax_id
            INNER JOIN account_tax_code tc ON tc.id = t.ref_base_code_id
            WHERE e.task_id = %s
              AND t.id = %s
              AND amount_net < 0
            """, (self.id, tax_code.id))
            
            for (amount_base_entries,) in cr.fetchall():
                amount_base += amount_base_entries
            
            # amount for taxes to pay
            cr.execute("""SELECT 
                COALESCE(SUM(amount_net),0.0)
            FROM account_period_entry e
            INNER JOIN account_tax t ON t.id = e.tax_id
            INNER JOIN account_tax_code tc ON tc.id = t.tax_code_id
            WHERE e.task_id = %s
              AND tc.id = %s
              AND amount_net > 0
            """, (self.id, tax_code.id))
            
            for (amount_tax_entries,) in cr.fetchall():
                amount_base += amount_tax_entries
            
            # amount for taxes refund
            cr.execute("""SELECT 
                COALESCE(SUM(amount_net),0.0)
            FROM account_period_entry e
            INNER JOIN account_tax t ON t.id = e.tax_id
            INNER JOIN account_tax_code tc ON tc.id = t.ref_tax_code_id
            WHERE e.task_id = %s
              AND tc.id = %s
              AND amount_net < 0
            """, (self.id, tax_code.id))
            
            for (amount_tax_entries,) in cr.fetchall():
                amount_tax += amount_tax_entries
            
            period_tax = period_tax_obj.create({
                "task_id": self.id,
                "sequence": tax_code.sequence,
                "name": tax_code.name,
                "code": tax_code.code,
                "amount_base": amount_base,
                "amount_tax": amount_tax,
                "parent_id": parent_id                
            })
            
            # process child
            childs = tax_code.child_ids
            if childs:
                for child in childs:
                    child_amount_base, child_amount_tax = calcTax(child, parent_id=period_tax.id)
                    if child.sign:
                        amount_base += (child_amount_base*child.sign)
                        amount_tax += (child_amount_tax*child.sign)
    
                # update amount after 
                # child processing
                period_tax.write({
                    "amount_base": amount_base,
                    "amount_tax": amount_tax
                })
                
            taskc.log("calculated tax | base: %s | tax: %s" % (amount_base, amount_tax), ref="account.tax.code,%s" % tax_code.id)
            return (amount_base, amount_tax) 
            
            
            
        
        for tax_code in tax_code_obj.search([("company_id","=",self.company_id.id),
                                             ("parent_id","=",False)]):
            calcTax(tax_code)
            
        taskc.done()
            
            
    def _run(self, taskc):
        journals = self.env["account.journal"].search([("periodic","=",True)])
        if not journals:
            taskc.logw("No journal for period processing specified.")
            return
        
        if self.period_id.company_id.taxation == 'invoice': 
            taskc.loge("**Tax on invoice** currently not supported.")
            return
       
        self._create_payment_based(taskc, journals)
        
        # delete all invalid entries
        invalid_entries = self.env["account.period.entry"].search([("task_id","=",self.id),
                                                 ("state","=","invalid")])
        taskc.logd("Delete invalid entries %s" % len(invalid_entries))
        invalid_entries.unlink()
                
        self._create_tax(taskc)
        
        

class AccountPeriodEntry(models.Model):
    _name = "account.period.entry"
    _description = "Period Entry"
    
    _rec_name = "move_id"
    _order = "date"
            
    task_id = fields.Many2one("account.period.task", "Task", required=True, index=True, readonly=True)
    move_id = fields.Many2one("account.move", "Move", index=True, required=True, readonly=True)
    
    date = fields.Date("Date", required=True, index=True, readonly=True)
    
    journal_id = fields.Many2one("account.journal", "Journal", index=True, required=True, readonly=True)
    account_id = fields.Many2one("account.account", "Account", index=True, required=True, readonly=True)
    invoice_id = fields.Many2one("account.invoice", "Invoice", index=True, readonly=True)
    voucher_id = fields.Many2one("account.voucher", "Receipt", index=True, readonly=True)
    
    tax_id = fields.Many2one("account.tax", "Tax", index=True, readonly=True)
   
    amount = fields.Float("Amount", digits=dp.get_precision("Account"), readonly=True)
    amount_gross = fields.Float("Gross Amount", digits=dp.get_precision("Account"), readonly=True)
    amount_net = fields.Float("Net Amount", digits=dp.get_precision("Account"), readonly=True)
    amount_tax = fields.Float("Tax Amount", digits=dp.get_precision("Account"), readonly=True)
    
    private_amount = fields.Float("Private Amount", digits=dp.get_precision("Account"), readonly=True)    
    
    payment_date = fields.Date("Payment Date", readonly=True)
    payment_amount = fields.Float("Payment", digits=dp.get_precision("Account"), readonly=True)    
    payment_rate = fields.Float("Payment Rate", readonly=True)
    payment_state = fields.Selection([("open","Open"),
                                      ("part", "Partly"),
                                      ("paid","Done")],
                                      string="Payment State",
                                      index=True, required=True, readonly=True)

    user_id = fields.Many2one("res.users", "Audited by", readonly=True)
        
    state = fields.Selection([("draft","Draft"),
                              ("valid","Validated"),
                              ("wrong","Wrong"),
                              ("invalid","Invalid")], string="Status",
                              default="draft",
                              readonly=True)
    
    currency_id = fields.Many2one("res.currency", "Currency", relation="company_id.currency_id", readonly=True)
    
    
    def _check_accountant(self):
        user = self.env.user
        if not user.has_group("account.group_account_user"):
            raise Warning(_("You must be an accountant to do that."))
        return user

    @api.multi
    def action_validate(self):
        user = self._check_accountant()
        for line in self.sudo():
            line.user_id = user
            line.state = "valid"
        return True
    
    @api.multi
    def action_wrong(self):
        user = self._check_accountant()
        for line in self.sudo():
            line.user_id = user
            line.state = "wrong"
        return True
    
    @api.multi
    def action_reset(self):
        user = self._check_accountant()
        for line in self.sudo():
            if line.user_id and line.user_id != user.id:
                if not user.has_group("account.group_account_manager"):
                    raise Warning(_("You must be an accountant manager to do that."))
            line.user_id = None
            line.state = "draft"
        return True
    
    
class AccountPeriodTax(models.Model):
    _name = "account.period.tax"
    _description = "Period Tax"
    _order = "sequence"
    
    task_id = fields.Many2one("account.period.task", "Task", required=True, readonly=True)
    
    name = fields.Char("Name", required=True, readonly=True)
    code = fields.Char("Code", readonly=True, index=True)

    sequence = fields.Integer("Sequence", default=10, readonly=True)
    parent_id = fields.Many2one("account.period.tax", "Parent", index=True, readonly=True)
    
    amount_base = fields.Float("Base Amount", readonly=True)
    amount_tax = fields.Float("Tax Amount", readonly=True)
    
    currency_id = fields.Many2one("res.currency", "Currency", relation="task_id.company_id.currency_id", readonly=True)
    entry_ids = fields.Many2many("account.period.entry", "account_period_tax_entry_rel",  "tax_id", "entry_id", 
                                 string="Entries", readonly=True)
    
    entry_count = fields.Integer("Entries", compute="_compute_entry_count", 
                                 store=False, readonly=True)
    
    @api.multi
    def _compute_entry_count(self):
        for task in self:
            self.entry_count = len(task.entry_ids)
    
    @api.multi
    def entry_action(self):
        for task in self:
            entry_ids = task.entry_ids.ids
            if entry_ids:
                return {
                    "display_name" : _("Entries"),
                    "view_type" : "form",
                    "view_mode" : "tree,form",
                    "res_model" : "account.period.entry",
                    "domain": [("id","in",entry_ids)],          
                    "type" : "ir.actions.act_window",
                }            
        return True
            
    
    