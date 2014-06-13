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

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.addons.at_base import format

class account_bank_statement(osv.osv):

    _inherit = "account.bank.statement"

    def button_confirm_bank(self, cr, uid, ids, context=None):
        res = super(account_bank_statement,self).button_confirm_bank(cr, uid, ids, context=context)
        move_obj = self.pool.get("account.move")
        for statement in self.browse(cr, uid, ids):
            for line in statement.line_ids:
                for move in line.move_ids:
                    move_obj.write(cr, uid, [move.id], {"date" : statement.date})
        return res

class account_bank_statement_compensation(osv.osv):

    _columns = {
        "name" : fields.char("Name",size=32,required=True),
        "sequence" : fields.integer("Sequence"),
        "journal_id" : fields.many2one("account.journal","Journal",required=True),
        "account_id" : fields.many2one("account.account","Account",required=True)
    }
    _name = "account.bank.statement.compensation"
    _description = "Bank Statement Compensation Option"
    _order = "sequence, id"


class account_bank_statement_line(osv.osv):

    def payment_view(self,cr, uid, ids, context=None):
        for statement_line in self.browse(cr, uid, ids, context=context):
            voucher = statement_line.voucher_id
            invoice = statement_line.invoice_id
            if voucher and invoice:
                return {
                    "name" : _("Payment"),
                    "view_type" : "form",
                    "view_mode" : "form",
                    "type" : "ir.actions.act_window",
                    "res_model" : "account.voucher",
                    "res_id" : voucher.id,
                    "target" : "current",
                    "context" : { "invoice_type" : invoice.type,
                                  "invoice_id" : invoice.id,
                                  "type" : invoice.type in ("out_invoice","out_refund") and "receipt" or "payment" },
                    "nodestroy": True,
                }
        return True

    def _invoice_id_get(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for line in self.browse(cr, uid, ids, context):
            invoice = line.voucher_id and line.voucher_id.invoice_id or None
            res[line.id]=invoice and invoice.id or None
        return res

    def _residual_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            voucher = obj.voucher_id
            if voucher and voucher.payment_option == "with_writeoff":
                res[obj.id]=voucher.writeoff_amount
        return res

    def _invoice_id_set(self, cr, uid, oid, field_name, field_value, arg, context=None):
        return True

    def onchange_invoice(self, cr, uid, ids, date, name, ref, journal_id, invoice_id, compensation_id, amount, voucher_id, context=None):
        res_value = {}
        res = { "value" : res_value }

        if amount:
            amount=abs(amount)

        #context
        if context is None:
            context = {}

        #check confirmed
        if ids:
            line = self.browse(cr, uid, ids[0], context)
            if line.statement_id.state == "confirm":
                return res

        #check journal
        if journal_id:
            voucher_obj = self.pool.get("account.voucher")
            voucher_line_obj = self.pool.get("account.voucher.line")
            invoice_obj = self.pool.get("account.invoice")
            compensation_obj = self.pool.get("account.bank.statement.compensation")
            journal_obj = self.pool.get("account.journal")
            partner_obj = self.pool.get("res.partner")
            move_line_obj = self.pool.get("account.move.line")

            journal = journal_obj.browse(cr,uid,journal_id,context=context)

            # delete voucher
            if not invoice_id and voucher_id:
                voucher_obj.unlink(cr, uid, [voucher_id], context=context)
            # create new voucher
            elif invoice_id:
                invoice = invoice_obj.browse(cr, uid, invoice_id, context=context)
                invoice_journal = invoice.journal_id
                if invoice.residual:
                    voucher_context = dict(context) or {}
                    currency = invoice.currency_id

                    company = invoice.company_id
                    residual_amount = invoice.type in ("out_refund", "in_refund") and -invoice.residual or invoice.residual
                    payment_rate = 1.0
                    payment_rate_currency = currency
                    voucher_type = invoice.type in ("out_invoice","out_refund") and "receipt" or "payment"
                    account_type = voucher_type == "payment" and "payable" or "receivable"
                    partner = partner_obj._find_accounting_partner(invoice.partner_id)

                    if not amount:
                        amount = residual_amount

                    voucher_context["payment_expected_currency"]=currency.id
                    voucher_context["default_partner_id"]=partner.id
                    voucher_context["default_amount"]= amount
                    voucher_context["default_type"]= voucher_type
                    voucher_context["type"]= voucher_type
                    voucher_context["invoice_id"]=invoice.id
                    voucher_context["journal_id"]=journal_id

                    #get move_lines from invoice
                    move_lines_ids = move_line_obj.search(cr, uid, [("move_id","=",invoice.move_id.id),("state","=","valid"), ("account_id.type", "=", account_type), ("reconcile_id", "=", False), ("partner_id", "=", partner.id)], context=context)
                    voucher_context["move_line_ids"]=move_lines_ids

                    #test if voucher is valid for invoice
                    if voucher_id:
                        voucher = voucher_obj.browse(cr,uid,voucher_id,context=context)
                        voucher_line_obj.unlink(cr,uid,[l.id for l in voucher.line_ids])
                        invoice_valid = False
                        for voucher_invoice in voucher.invoice_ids:
                            if voucher_invoice.id == invoice_id:
                                invoice_valid = True
                                break

                        if not invoice_valid:
                            voucher_obj.unlink(cr, uid, [voucher_id], context=context)
                            voucher_id = None

                    data = { "payment_option" : "without_writeoff",
                             "comment" : _("Write-Off"),
                             "journal_id" : journal.id }

                    if date:
                        data["date"]=date

                    data.update(voucher_obj.onchange_partner_id(cr, uid, [], invoice.partner_id.id,
                                              journal.id, amount, currency.id, voucher_type, date,
                                              context=voucher_context)["value"])

                    data.update(voucher_obj.onchange_amount(cr, uid, [], amount, payment_rate,
                                              partner.id, journal.id, currency.id, voucher_type, date,
                                              payment_rate_currency.id, company.id, context=voucher_context)["value"])

                    if voucher_type == "receipt":
                        line_datas_field = "line_cr_ids"
                        line_datas = data.get("line_cr_ids",[])
                        data.pop("line_dr_ids",None)
                        sign=1.0
                    else:
                        line_datas_field = "line_dr_ids"
                        line_datas = data.get("line_dr_ids",[])
                        data.pop("line_cr_ids",None)
                        sign=-1.0

                    if len(line_datas) == 1:
                        line_datas[0]["amount"]=residual_amount
                        # compensation
                        if compensation_id:
                            compensation = compensation_obj.browse(cr,uid,compensation_id,context=context)
                            data["payment_option"]="with_writeoff"
                            data["writeoff_acc_id"]=compensation.account_id.id
                            data["comment"]=compensation.name


                    data.update(voucher_obj.onchange_journal(cr, uid, [], journal.id, [],
                                              False, invoice.partner_id.id, date, amount, voucher_type, company.id, context=voucher_context)["value"])

                    data.update(voucher_obj.onchange_date(cr, uid, [], date, currency.id, payment_rate_currency.id, amount, company.id, context=voucher_context)["value"])

                    if line_datas:
                        data[line_datas_field] = [(0,0,l) for l in line_datas]

                    #if no voucher id exist create one
                    if not voucher_id:
                        voucher_id = voucher_obj.create(cr,uid,data,voucher_context)
                    else:
                        voucher_obj.write(cr,uid,voucher_id,data,voucher_context)

                    # result
                    voucher = voucher_obj.browse(cr,uid,voucher_id,context=context)
                    res_value["voucher_id"]=voucher_id
                    res_value["invoice_id"]=invoice_id
                    res_value["account_id"]=invoice.account_id.id
                    res_value["partner_id"]=invoice.partner_id.id
                    res_value["amount"]=amount*sign
                    res_value["residual_amount"]=voucher.writeoff_amount

                    #if not name:
                    res_value["name"]=invoice.move_id.name
                    #if not ref:
                    res_value["ref"]=invoice.reference

                    #type
                    if invoice_journal.type == "sale":
                        res_value["type"] = "customer"
                    elif invoice_journal.type == "purchase":
                        res_value["type"] = "supplier"
                    else:
                        res_value["type"] = "general"

                # delete voucher if no invoice
                elif voucher_id:
                    res_value["voucher_id"]=None
                    voucher_obj.unlink(cr, uid, [voucher_id], context=context)

        # update compensation
        return res



    _columns = {
        "voucher_id" : fields.many2one("account.voucher", "Voucher"),
        "invoice_id" : fields.function(_invoice_id_get, fnct_inv=_invoice_id_set, type="many2one", obj="account.invoice",
                                       string="Invoice", store=False,
                                       domain=[("state","=","open")]),

        "residual_amount" : fields.function(_residual_amount, type="float",
                                            string="Rest", store=False, readonly=True ),

        "compensation_id" : fields.many2one("account.bank.statement.compensation","Compensation")
    }
    _inherit = "account.bank.statement.line"


class account_voucher(osv.osv):

    def _invoice_ids(self, cr, uid, ids, field_name, arg, context=None):
        cr.execute(" SELECT v.id, inv.id FROM account_invoice inv "
                   " INNER JOIN account_move m ON m.id = inv.move_id "
                   " INNER JOIN account_move_line ml ON ml.move_id = m.id "
                   " INNER JOIN account_voucher_line vl ON vl.move_line_id = ml.id "
                   " INNER JOIN account_voucher v ON v.id = vl.voucher_id AND v.id IN %s "
                   " GROUP BY 1,2", (tuple(ids),))

        res = dict([(i,[]) for i in ids])
        for row in cr.fetchall():
            res[row[0]].append(row[1])
        return res

    def _invoice_id(self, cr, uid, ids, field_name, arg, context=None):
        invoice_ids = self._invoice_ids(cr, uid, ids, field_name, arg, context)
        res = dict([(i,invoice_ids[i] and invoice_ids[i][0] or None) for i in ids])
        return res

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if context is None:
            context = {}
        f = format.LangFormat(cr, uid, context=context)
        amount_datas = self.read(cr, uid, ids, ["amount"], context=context)
        for amount_data in amount_datas:
            res.append( (amount_data["id"],f.formatLang(amount_data["amount"])) )
        return res

    _inherit = "account.voucher"
    _columns = {
        "invoice_id" : fields.function(_invoice_id, type="many2one", obj="account.invoice",
                                       readonly=True, string="Invoice"),
        "invoice_ids" : fields.function(_invoice_ids, type="many2many",
                                        obj="account.invoice", readonly=True, string="Invoices")
    }

