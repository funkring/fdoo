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

import re
import base64
import csv
import datetime
from cStringIO import StringIO

from openerp import models, fields, api, _


class BmdReconcilProfile(models.Model):
    _name = "bmd.reconcil.profile"
    _description = "BMD OP. Profil"

    name = fields.Char("Name", required=True)
    company_id = fields.Many2one(
        "res.company",
        "Firma",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "bmd.reconcil.profile"
        ),
    )

    journal_id = fields.Many2one("account.journal", "Journal", required=True)
    exclude = fields.Char("Ignoriere Kennzeichen")


class BmdReconcil(models.Model):
    _name = "bmd.reconcil"
    _description = "BMD OP. Ausgleich"
    _inherit = ["util.time"]
    _inherits = {"automation.task": "task_id"}
    _order = "id desc"

    @api.model
    def _default_profile(self):
        company_id = self.env["res.company"]._company_default_get(
            "bmd.reconcil.profile"
        )
        return self.env["bmd.reconcil.profile"].search(
            [("company_id", "=", company_id)], limit=1
        )

    task_id = fields.Many2one(
        "automation.task", "Task", required=True, index=True, ondelete="cascade"
    )
    profile_id = fields.Many2one(
        "bmd.reconcil.profile",
        "Profil",
        required=True,
        ondelete="restrict",
        default=_default_profile,
    )

    reconciled = fields.Integer(
        "Reconciled", compute="_compute_reconciled", store=False
    )

    csv_data = fields.Binary("CSV Datei", required=True)
    csv_data_fname = fields.Char("CSV Dateiname")

    @api.onchange("profile_id")
    def _onchange_period_profile(self):
        name = [self._currentDate()]
        if self.profile_id:
            name.append(self.profile_id.name)
        name = " ".join(name)
        self.name = name

    @api.model
    @api.returns("self", lambda self: self.id)
    def create(self, vals):
        res = super(BmdReconcil, self).create(vals)
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
        res = super(BmdReconcil, self).unlink()
        self.env["automation.task"].browse(task_ids).unlink()
        return res

    def _run_options(self):
        return {"stages": 1, "singleton": True}

    def _run(self, taskc):
        taskc.stage("Lade")

        csv_data = base64.decodestring(self.csv_data)
        csv_data = unicode(csv_data, "iso8859-15").encode("UTF-8")
        csv_data = StringIO(csv_data)
        try:
            date = None
            open_date = None
            date_pattern = re.compile("per ([0-9]{1,2})\\. (\w+) ([0-9]{4})")
            month_dict = {
                "Jänner": "01",
                "Februar": "02",
                "März": "03",
                "April": "04",
                "Mai": "05",
                "Juni": "06",
                "Juli": "07",
                "August": "08",
                "September": "09",
                "Oktober": "10",
                "November": "11",
                "Dezember": "12",
            }
    
            reader = csv.reader(csv_data, delimiter=";", quotechar=None)
            fields = {
                "Kto-Nr": None,
                "Rng-Nr": None,
                "Rng-Betrag": None,
                "OP-Betrag": None,
                "Text": None,
                "BS": None,
                "Rng-Dat": None,
            }
    
            initialized = False
            last_col = 0
            row_n = 0
    
            numbers = []
            invoice_obj = self.env["account.invoice"]
    
            exclude = self.profile_id.exclude or ""
            exclude = set(exclude.split(","))
    
            def parseStr(val):
                if not val:
                    return ""
                if not isinstance(val, basestring):
                    val = str(val)
                return val.strip()
    
            def parseFloat(val):
                if not val:
                    return ""
                return float(val.strip())
    
            for row in reader:
                row_n += 1
                if date is None:
                    if len(row) >= 3 and row[2]:
                        res = date_pattern.search(row[2])
                        if res:
                            day = res.group(1).zfill(2)
                            month = month_dict[res.group(2)]
                            year = res.group(3).zfill(4)
                            date = "%s-%s-%s" % (year, month, day)
    
                elif not initialized:
                    found = 0
                    for i, cell in enumerate(row):
                        if not cell:
                            continue
                        cell = cell.strip()
                        if cell in fields:
                            fields[cell] = i
                            last_col = i
                            found += 1
    
                    initialized = found == len(fields)
    
                else:
    
                    if len(row) <= last_col or not row[0] or not row[0].strip():
                        continue
    
                    bs = parseStr(row[fields["BS"]])
                    if bs in exclude:
                        continue
    
                    number = parseStr(row[fields["Rng-Nr"]])
                    if not number:
                        Warning("Rechnungsnummer in Zeile %s ist leer" % row_n)
    
                    text = parseStr(row[fields["Text"]])
                    if not text:
                        Warning("Text in Zeile %s ist leer" % row_n)
    
                    # check if has the right number
                    if text.find(number) >= 0 and len(number) > 3:
                        numbers.append(number)
    
                    # parse date
                    invoice_date = parseStr(row[fields["Rng-Dat"]])
                    if invoice_date:
                        invoice_date = datetime.datetime.strptime(
                            invoice_date, "%y/%m/%d"
                        ).strftime("%Y-%m-%d")
                        if invoice_date:
                            if not open_date:
                                open_date = invoice_date
                            else:
                                open_date = max(invoice_date, open_date)
    
                    # partner_ref = parseStr(row[fields["Kto-Nr"]])
                    # amount = parseFloat(row[fields["Rng-Betrag"]])
                    # balance =  parseFloat(row[fields["OP-Betrag"]])
    
            if date and open_date:
                date = min(date, self._nextDay(open_date))
    
            if not date:
                raise Warning("Es wurde kein Datum gefunden!")
            if not initialized:
                raise Warning("Es wurden keine Daten gefunden!")
    
            inv_type = "out_invoice"
            company_id = self.profile_id.company_id.id
            journal_id = self.profile_id.journal_id.id
    
            # check invoices
            domain = [
                ("company_id", "=", company_id),
                ("date_invoice", "<", date),
                ("type", "=", inv_type),
                ("state", "=", "open"),
            ]
            if numbers:
                domain.append(("number", "not in", numbers))
                check_domain = [
                    ("company_id", "=", company_id),
                    ("type", "=", inv_type),
                    ("number", "in", numbers),
                ]
                found_invoice_count = invoice_obj.search(check_domain, count=True)
                if found_invoice_count != len(numbers):
                    found_invoice_vals = invoice_obj.search_read(check_domain, ["number"])
                    found_invoice_numbers = set([v["number"] for v in found_invoice_vals])
                    not_found_numbers = list(set(numbers).difference(found_invoice_numbers))
                    like_found_numbers = set()
                    for notfound_num in not_found_numbers:
                        notfound_vals = invoice_obj.search_read(
                            [("number", "like", notfound_num)], ["number"]
                        )
                        for notfound_val in notfound_vals:
                            numbers.append(notfound_val["number"])
                            like_found_numbers.add(notfound_num)
                            
                    not_found_numbers = list(set(not_found_numbers) - like_found_numbers)
                    if not_found_numbers:
                        raise Warning(
                            "Es konnten nicht alle Rechnungen gefunden werden:\n %s"
                            % ", ".join(not_found_numbers)
                        )
    
                taskc.log("Offene Rechnungen %s" % found_invoice_count)
    
            # reconcile invoices
            voucher_obj = self.env["account.voucher"]
    
            taskc.done()
    
            taskc.stage("Ausgleich")
            invoices = invoice_obj.search(domain, order="date_invoice desc")
    
            taskc.initLoop(len(invoices))
            for inv in invoices:
    
                if not inv.account_id.reconcile:
                    taskc.logw(
                        "Setze Konto ausgleichbar",
                        ref="account.account,%s" % inv.account_id.id,
                    )
                    inv.account_id.reconcile = True
    
                try:
                    taskc.log("Ausgleich von Rechnung", ref="account.invoice,%s" % inv.id)
                    res = inv.invoice_pay_customer()
                    
                    voucher_ctx = dict(self._context)
                    voucher_ctx.update(res["context"])
    
                    partner_id = voucher_ctx["default_partner_id"]
                    amount = voucher_ctx["default_amount"]
                    voucher_type = voucher_ctx["type"]
    
                    res = voucher_obj.onchange_journal_voucher(
                        partner_id=partner_id,
                        price=amount,
                        journal_id=journal_id,
                        ttype=voucher_type,
                        company_id=company_id,
                        context=voucher_ctx,
                    )
    
                    values = res["value"]
                    values["journal_id"] = journal_id
    
                    def conv_ids(name):
                        if name in values:
                            values[name] = [(0, 0, v) for v in values[name]]
    
                    conv_ids("line_cr_ids")
                    conv_ids("line_dr_ids")
    
                    voucher = voucher_obj.with_context(voucher_ctx).create(values)
                    voucher.button_proforma_voucher()
    
                    inv.bmd_reconcil_id = self.id
                except Exception as e:
                    taskc.loge(
                        "Fehler beim Ausgleich der Rechnung",
                        ref="account.invoice,%s" % inv.id,
                    )
                    raise e
    
                taskc.nextLoop()
    
            taskc.done()
            
        finally:
            csv_data.close()

    @api.multi
    def _compute_reconciled(self):
        invoice_obj = self.env["account.invoice"]
        for obj in self:
            obj.reconciled = invoice_obj.search([("bmd_reconcil_id","=",self.id)],count=True)
