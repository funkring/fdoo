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

import re
import base64
from cStringIO import StringIO

from datetime import datetime
from datetime import date

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.tools import ustr


class ExporterException(Exception):
    pass


class Exporter(object):
    def writeln(self, data):
        pass


class CsvExport(Exporter):
    def __init__(self, buf):
        self.buf = buf
        self.lf = "\r\n"
        self._write_fct = self._writeln_header

    def _write_header(self, data):
        self._write_fct = self.writeln
        for data_field in data:
            self.buf.write(data_field[0])
            self.buf.write(";")

        self.buf.write(self.lf)

    def _write(self, data):
        for data_field in data:
            value = data_field[1]

            if isinstance(value, date):
                self.buf.write(datetime.strftime(value, "%Y%m%d"))
            elif isinstance(value, float):
                self.buf.write(("%.2f" % value).replace(".", ","))
            elif isinstance(value, basestring):
                self.buf.write(value)
            else:
                self.buf.write(str(value))

            self.buf.write(";")

        self.buf.write(self.lf)

    def writeln(self, data):
        self._write_fct(data)


class FixLenExport(Exporter):
    def __init__(self, buf):
        self.buf = buf
        self.lf = "\r\n"

    def writeln(self, data):
        line = ""
        for data_field in data:
            if len(data_field) == 5:
                (name, value, width, start, end) = data_field

                if isinstance(value, (int, long)):
                    if len(line) + 1 != start:
                        raise ExporterException(
                            "Wrong position at %s: %d != %d" % (name, len(line), start)
                        )

                    self.line += ustr(value or "").rjust(width, "0")[:width]

                    if len(line) != end:
                        raise ExporterException(
                            "Wrong position at %s: %d != %d" % (name, len(line), end)
                        )

                else:
                    if len(line) + 1 != start:
                        raise ExporterException(
                            "Wrong position at %s: %d != %d" % (name, len(line), start)
                        )
                    value = value or ""
                    value = value.strip()
                    line += ustr(value).ljust(width, " ")[:width]
                    if len(line) != end:
                        raise ExporterException(
                            "Wrong position at %s: %d != %d" % (name, len(line), end)
                        )

            elif len(data_field) == 7:
                (name, value, width, pre, post, start, end) = value
                el = str(float(value or 0.0)).split(".")
                line += el[0].rjust(pre, "0")
                line += el[1].ljust(post, "0")

                if pre + post != width:
                    line += value >= 0.0 and "+" or "-"

                if len(line) != end:
                    raise Warning(
                        "Wrong position at %s: %d != %d" % (name, len(line), end)
                    )

            self.buf.write(line)
            self.buf.write(self.lf)


class BmdExportFile(models.BaseModel):
    _name = "bmd.export.file"
    _inherits = {"ir.attachment": "attachment_id"}
    _rec_name = "export_name"

    export_name = fields.Char("Export Name", required=True, index=True)
    bmd_export_id = fields.Many2one("bmd.export", "Export", required=True, index=True)
    attachment_id = fields.Many2one(
        "ir.attachment", "Attachment", required=True, index=True, ondelete="cascade"
    )


class BmdExport(models.BaseModel):
    _name = "bmd.export"
    _inherit = ["mail.thread", "util.time", "util.report"]

    _description = "BMD Export"
    _inherits = {"automation.task": "task_id"}
    
    _re_belegnr =  [re.compile("^.*[^0-9]([0-9]+)$"),
                    re.compile("^([0-9]+)$")]


    @api.model
    def _default_profile(self):
        company_id = self.env['res.company']._company_default_get("bmd.export.profile")
        return self.env["bmd.export.profile"].search([("company_id","=",company_id)], limit=1)
    
    @api.model
    def _default_period(self):
        period_start = self._firstOfLastMonth()
        period_obj = self.env["account.period"]
        
        period = period_obj.search([("date_start","=",period_start)], limit=1)
        if not period:
            period = period_obj.search([], limit=1, order="date_start desc")
        
        return period
    
    @api.onchange("period_id", "profile_id")
    def _onchange_period_profile(self):
        name = []
        if self.period_id:
            name.append(self.period_id.name)
        if self.profile_id:
            name.append(self.profile_id.name)
        name = " ".join(name)
        self.name = name
        

    task_id = fields.Many2one(
        "automation.task", "Task", required=True, index=True, ondelete="cascade"
    )
    period_id = fields.Many2one("account.period", "Periode", required=True,
                                ondelete="restrict",
                                default=_default_period)
    
    profile_id = fields.Many2one("bmd.export.profile", "Profil", 
        ondelete="restrict", required=True, default=_default_profile
    )
    
    company_id = fields.Many2one("res.company", "Company", relation="profile_id.company_id", 
                                 readonly=True)

    line_ids = fields.One2many("bmd.export.line", "bmd_export_id", "BMD Export Zeilen")
    export_lines = fields.Integer(
        "Export Zeilen", compute="_compute_export_lines", store=False
    )
    
    export_file_ids = fields.One2many("bmd.export.file", "bmd_export_id", "Export Datei(en)")
    number_from = fields.Char("Ab Nummer")

    @api.model
    @api.returns("self", lambda self: self.id)
    def create(self, vals):
        res = super(BmdExport, self).create(vals)
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
        res = super(BmdExport, self).unlink()
        self.env["automation.task"].browse(task_ids).unlink()
        return res

    def _run_options(self):
        return {"stages": 3, "singleton": True}

    def _run(self, taskc):
        taskc.stage("Vorbereitung")
        self._create_lines(taskc)
        taskc.done()

        if self.profile_id.version == "ntcs":
            taskc.stage("NTCS Export")
            self._export_ntcs(taskc)
            taskc.done()
        else:
            taskc.stage("BMD55 Export")
            self._export_bmd5(taskc)
            taskc.done()

        taskc.stage("Berichte")
        self._create_reports(taskc)
        taskc.done()

    @api.multi
    def _compute_export_lines(self):
        for obj in self.objects:
            obj.export_line_count = len(obj.line_ids)

    
    def _sanitize_belegnr(self, value):
        if value:
            value = value.replace("/","")
            for re_belegnr in self._re_belegnr:
                result = re_belegnr.match(value)
                if result:
                    return result.group(1)
        return None

    def _export_file(self, taskc, export_name, file_name, data=None, datas=None):
        export_obj = self.env["bmd.export.file"]
        export_file = export_obj.search(
            [("bmd_export_id", "=", self.id), ("export_name", "=", export_name)], limit=1
        )
        values = {
            "export_name": export_name,
            "datas": data and base64.encodestring(data) or datas,
            "name": file_name,
            "datas_fname": file_name,
            "res_model": "bmd.export",
            "res_id": self.id,
            "bmd_export_id": self.id
        }

        if export_file:
            export_file.write(values)
        else:
            export_file = export_obj.create(values)
        return export_file

    def _export_buerf(self, taskc):
        buf = StringIO.StringIO()
        try:
            exp = CsvExport(buf)
            for line in self.line_ids:
                exp.writeln(
                    (
                        ("konto", line.konto),
                        ("buchdat", self._strToDate(line.buchdat)),
                        ("gkto", line.gkto),
                        ("belegnr", line.belegnr),
                        ("belegdat", self._strToDate(line.belegdat)),
                        ("mwst", line.mwst),
                        ("bucod", line.bucod),
                        ("betrag", line.betrag or 0.0)("steuer", line.steuer or 0.0),
                        ("text", line.text),
                        ("zziel", line.zziel or 0),
                        ("symbol", line.symbol),
                        ("gegenbuchkz", line.gegenbuchkz),
                        ("verbuchkz", line.verbuchkz),
                        ("steucod", line.steucod),
                    )
                )
            return self._export_file(
                taskc,
                "buerf",
                "buerf",
                data=buf.getvalue().encode("cp1252", "ignore"),
                taskc=taskc,
            )
        finally:
            buf.close()

    def _export_stamerf(self, taskc):
        ir_property = self.env["ir.property"]
        default_partner_receivable = ir_property.get("property_account_receivable","res.partner")
        default_partner_payable_id =  ir_property.get("property_account_payable","res.partner")

        
        buf = StringIO.StringIO()
        exp = FixLenExport(buf)
        try:
            company = self.period_id.company_id
            profile = self.profile_id
            company_country = company.country_id

            partners = self.mapped("line_ids.partner_id") | self.mapped(
                "line_ids.partner_id.commercial_partner_id"
            )

            for partner in partners:

                partner_account_codes = []
                payable_account = partner.property_account_payable
                receivable_account = partner.property_account_receivable

                if (
                    payable_account
                    and payable_account.code
                    and len(payable_account.code) > 4
                ):
                    if (
                        not default_partner_payable_id
                        or default_partner_payable_id.id != payable_account.id
                    ):
                        partner_account_codes.append(payable_account.code)

                if (
                    receivable_account
                    and receivable_account.code
                    and len(receivable_account.code) > 4
                ):
                    if (
                        not default_partner_receivable
                        or default_partner_receivable.id != receivable_account.id
                    ):
                        partner_account_codes.append(receivable_account.code)

                cession_code = None
                if partner.customer:
                    cession_code = profile.cession_code

                if profile.partner_name_as_matchcode:
                    matchcode = partner.name
                else:
                    matchcode = partner.ref

                for account_code in partner_account_codes:
                    country = partner.country_id
                    foreigner = False
                    country_code = ""
                    if not country:
                        taskc.logw(
                            "Kein Land für Partner gesetzt",
                            ref="res.partner,%s" % partner.id,
                        )
                    else:
                        country_code = country.code
                        if country:
                            foreigner = country.id != company_country.id

                    discount_days = 0
                    discount_percent = 0.0
                    payment_days = 0

                    exp.writeln(
                        (
                            ("1-kontonummer", account_code or "", 9, 1, 9),
                            ("4-name", partner.name or "", 35, 10, 44),
                            ("5-matchcode", matchcode or "", 20, 45, 64),
                            (
                                "11-titel",
                                partner.title and partner.title.name or "",
                                15,
                                65,
                                79,
                            ),
                            ("5-beruf", "", 35, 80, 114),
                            (
                                "6-strasse",
                                partner and partner.street or "",
                                30,
                                115,
                                144,
                            ),
                            ("7-plz", partner and partner.zip or "", 12, 145, 156),
                            ("8-ort", partner and partner.city or "", 20, 157, 176),
                            ("9-postfach", "", 20, 177, 196),
                            ("10-postfach-plz", "", 12, 197, 208),
                            ("59-strassenkz", "", 4, 209, 212),
                            ("12-staat", country_code, 3, 213, 215),
                            ("13-kontaktperson", partner.name or "", 30, 216, 245),
                            ("14-telefonnummer", partner.phone or "", 18, 246, 263),
                            ("15-telefax", partner.fax or "", 18, 264, 281),
                            ("16-email", partner.email or "", 50, 282, 331),
                            ("17-internet", "", 35, 332, 366),
                            ("40-bankkonto", "", 20, 367, 386),
                            ("41-blz", "", 12, 387, 398),
                            ("52-iban", "", 34, 399, 432),
                            ("42-swift", "", 12, 433, 444),
                            ("49-bank-land", "", 2, 445, 446),
                            ("18-ustid", partner.vat or "", 15, 447, 461),
                            ("53-zessionkz", cession_code, 1, 462, 462),
                            ("65-datum", "", 8, 463, 470),
                            ("43-zahlsperre", "", 2, 471, 472),
                            ("44-zahlspesen", "", 2, 473, 474),
                            ("45-zahlgrund", "", 2, 475, 476),
                            ("46-zahlumsatzpos", "", 4, 477, 480),
                            ("47-zahlueberweisungsart", "", 2, 481, 482),
                            ("48-zahlbank", "", 4, 483, 486),
                            ("50-bankeinzug", "", 4, 487, 490),
                            ("51-fremdkonto", "", 9, 491, 499),
                            ("20-auslaender", (foreigner and "1") or "", 2, 500, 501),
                            ("21-keinesteuer", "", 2, 502, 503),
                            ("22-zahlungsziel", payment_days, 6, 504, 509),
                            ("23-skonto", discount_percent, 5, 3, 2, 510, 514),
                            ("26-skontotage", discount_days, 4, 515, 518),
                            ("23-skonto2", "", 5, 519, 523),
                            ("26-skontotage2", "", 4, 524, 527),
                            ("28-kondition", "", 4, 528, 531),
                            ("27-tol-proz", 0.0, 5, 3, 2, 532, 536),
                            ("30-mahnsperre", "", 2, 537, 538),
                            ("31-mahnkosten", "", 2, 539, 540),
                            ("32-mahnverbuchkz", "", 2, 541, 542),
                            ("33-mahndatum", "", 8, 543, 550),
                            ("34-mahnformular", "", 4, 551, 554),
                            ("35-mahnkontoauszug", "", 2, 555, 556),
                            ("27-bonitaet", "", 4, 557, 560),
                            ("39-gegenverrechnungs-konto", "", 9, 561, 569),
                            ("54-divcode", "", 2, 570, 571),
                            ("55-kkreis", "1", 2, 572, 573),
                            ("56-sammelkonto", "", 9, 574, 582),
                            ("57-rechnungskonto", "", 9, 583, 591),
                            ("19-uid-datum", "", 8, 592, 599),
                            ("60-firmen-anrede", "", 4, 600, 603),
                            ("61-persoenl-anrede", "", 4, 604, 607),
                            ("62-zu-handen-anrede", "", 4, 608, 611),
                            ("63-brief-anrede", "", 4, 612, 615),
                            ("66-branchenkz", "", 4, 616, 619),
                            ("67-vertreter1", "", 6, 620, 625),
                            ("68-vertreter2", "", 6, 626, 631),
                            ("69-versandart", "", 4, 632, 635),
                            ("70-verkaufsgebiet", "", 4, 636, 639),
                            ("71-handelsring", "", 4, 640, 643),
                            ("72-km-entf", "", 4, 644, 647),
                            ("73-rabatt-code", "", 4, 648, 651),
                            ("74-rabatt", 0.0, 9, 6, 2, 652, 660),
                            ("75-auftragsstand", 0.0, 18, 15, 2, 661, 678),
                            ("76-kreditlimit", 0.0, 18, 15, 2, 679, 696),
                            ("77-wechselobligo", 0.0, 18, 15, 2, 697, 714),
                            ("64-staaten-nummer", "", 4, 715, 718),
                            ("79-fipkurz-zahlmodus", "", 2, 719, 720),
                            ("208-varcode1", "", 4, 721, 724),
                            ("206-umstkonto", "", 10, 725, 734),
                            ("226-DGNR", "", 9, 735, 743),
                            ("Platzhalter", "", 135, 744, 878),
                            ("213-DL-Code", "", 4, 879, 882),
                            ("NTCS-Kontogruppe", "", 1, 883, 883),
                            ("210-Zweitwaehrung", "", 4, 884, 887),
                            ("220 - Freifeld alf1", "", 20, 888, 907),
                            ("221 - Freifeld alf2", "", 20, 908, 927),
                            ("222 - Freifeld alf3", "", 1, 928, 928),
                            ("223 - Freifeld num1", 0.0, 18, 16, 2, 929, 946),
                            ("224 - Freifeld num2", 0.0, 18, 15, 2, 947, 964),
                            ("225 - Freifeld num3", "", 4, 965, 968),
                            ("209 - Varcode2", "", 9, 969, 977),
                            ("201 - Fremdwaehrungs-Code", "", 4, 978, 981),
                            ("202 - Landkennz", "", 4, 982, 985),
                            ("205 - EB-Buchkonto", "", 9, 986, 994),
                            ("203 - Buchsperre", "", 2, 995, 996),
                            ("207 - EB-Uebernahme-Kz", "", 2, 997, 998),
                            ("Loeschkz", "", 1, 999, 999),
                            ("Kontrollkenzeichen", "*", 1, 1000, 1000),
                        )
                    )

                return self._export_file(
                    taskc,
                    "stamerf",
                    "stamerf",
                    data=buf.getvalue().encode("cp1252", "ignore"),
                    taskc=taskc,
                )

        finally:
            buf.close()

    def _export_bmd5(self, taskc=None):
        pass

    def _export_ntcs(self, taskc=None):
        pass

    def _create_lines(self, taskc=None):
        # unlink privious lines
        self.line_ids.unlink()

        cr = self._cr
        
        invoice_obj = self.env["account.invoice"]
        move_obj = self.env["account.move"]
        account_obj = self.env["account.account"]
        fpos_obj = self.env["account.fiscal.position"]
        line_obj = self.env["bmd.export.line"]

        period_id = self.period_id.id
        profile = self.profile_id
        receipt_primary = profile.receipt_primary

        class BmdAccountData:
            """ Helper class """

            def __init__(self, account_code, tax, steucod, amount=0.0, amount_tax=0.0):
                self.code = account_code
                self.tax = tax
                self.tax_value = int(tax.amount * 100) if tax else 0   
                self.steucod = steucod
                self.amount = amount
                self.amount_tax = amount_tax                

        def exportInvoice(invoice):
            company = invoice.company_id
            account_payable = invoice.partner_id.property_account_payable
            account_receivable = invoice.partner_id.property_account_receivable
            country = invoice.partner_id.country_id
            foreigner = country and company.country_id.id != country.id
            european_union = False

            if foreigner and invoice.partner_id.vat:
                european_union = True

            area = "I"
            if foreigner:
                if european_union:
                    area = "EU"
                elif invoice.type in ["out_invoice", "out_refund"]:
                    area = "A"
                else:
                    area = "D"

            bmd_text = [invoice.number]
            if invoice.name:
                bmd_text.append(invoice.name)

            # check/trim period
            period = invoice.period_id
            bookingdate = invoice.date_invoice
            if bookingdate < period.date_start or bookingdate > period.date_stop:
                bookingdate = period.date_stop

            bmd_line = {
                "bereich": area,
                "satzart": "0",
                "invoice_id": invoice.id,
                "partner_id": invoice.partner_id.id,
                "buchdat": bookingdate,
                "belegdat": invoice.date_invoice,
                "belegnr": self._sanitize_belegnr(invoice.number),
                "bucod": "1",
                "zziel": "0",
                "text": ":".join(bmd_text),
                "gegenbuchkz": "E",
                "verbuchkz": "A",
                "symbol": (invoice.journal_id and invoice.journal_id.code) or "",
            }

            sign = 1.0
            if invoice.type == "out_refund":
                sign = -1.0

            if invoice.type in ("in_refund", "in_invoice"):
                if invoice.type == "in_invoice":
                    sign = -1
                bmd_line["bucod"] = "2"
                bmd_line["ebkennz"] = "1"
                bmd_line["konto"] = account_payable and account_payable.code or ""
            else:
                bmd_line["konto"] = account_receivable and account_receivable.code or ""

            if invoice.date_due and invoice.date_invoice:
                bmd_line["zziel"] = (
                    self._strToDate(invoice.date_due)
                    - self._strToDate(invoice.date_invoice)
                ).days

            accounts = {}
            for line in invoice.invoice_line:
                account = line.account_id
                taxes = line.invoice_line_tax_id
                product = line.product_id
                steucod = ""

                # Eingangs- bzw. Lieferanten Rechnungen
                if invoice.type in ["in_invoice", "in_refund"]:
                    # Für Produkt Eingang/Import werden die lokalen Steuern des Produkt/Mapping verwendet
                    if foreigner:
                        if product:
                            taxes = line.product_tax_ids
                        # Wenn kein Produkt angegeben wurde, wird ein reverse mapping der Steuer versucht
                        # falls ein Steuermapping verwendet wird
                        elif invoice.fiscal_position:
                            try:
                                taxes = fpos_obj.unmap_tax(
                                    invoice.fiscal_position, taxes
                                )
                            except Exception:
                                raise Warning(
                                    "Steuerumschlüsselungsfehler bei Rechnung %s"
                                    % invoice.number
                                )

                    if european_union:
                        steucod = (
                            "09"  # Einkauf innergem. Erwerb, wenn VSt-Abzug besteht
                        )

                    if product:
                        if european_union and product.type == "service":
                            steucod = "19"  # Reverse Charge mit Vorsteuer"

                # Ausgangs- bzw. Rechnungen an Kunden
                elif invoice.type in ["out_invoice", "out_refund"]:
                    if european_union:
                        steucod = "07"  # Innergemeinschaftliche Lieferung

                tax = None
                if taxes:
                    tax = taxes[0]
                
                account_key = (account.code, tax and tax.id or 0, steucod)
                account_data = accounts.get(account_key)
                if not account_data:
                    account_data = BmdAccountData(account.code, tax, steucod)
                    accounts[account_key] = account_data

                line_total = taxes.compute_all(
                    line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                    line.quantity,
                    product=line.product_id.id,
                    partner=line.invoice_id.partner_id.id,
                )

                line_sum = line.price_subtotal_taxed
                line_tax = line_total["total_included"] - line_total["total"]

                account_data.amount += line_sum
                account_data.amount_tax += line_tax

            def addExportLine(account_data):
                bmd_line_copy = bmd_line.copy()
                bmd_line_copy["gkto"] = account_data.code
                bmd_line_copy["betrag"] = account_data.amount * sign
                bmd_line_copy["mwst"] = account_data.tax_value
                bmd_line_copy["steuer"] = round(
                    (-1.0 * sign) * account_data.amount_tax, 2
                )

                if account_data.steucod:
                    bmd_line_copy["steucod"] = account_data.steucod

                if receipt_primary:
                    if bmd_line_copy["bucod"] == "1":
                        bmd_line_copy["bucod"] = "2"
                    if bmd_line_copy["bucod"] == "2":
                        bmd_line_copy["bucod"] = "1"
                    tmp = bmd_line_copy["konto"]
                    bmd_line_copy["konto"] = bmd_line_copy["gkto"]
                    bmd_line_copy["gkto"] = tmp
                    bmd_line_copy["betrag"] = bmd_line_copy["betrag"] * -1.0
                    bmd_line_copy["steuer"] = bmd_line_copy["steuer"] * -1.0

                # Steuern auf Null setzen wenn Drittland
                if area == "D":
                    bmd_line_copy["mwst"] = 0
                    bmd_line_copy["steuer"] = 0.0

                bmd_line_copy["account_id"] = account_obj.search(
                    [
                        ("company_id", "=", company.id),
                        ("code", "=", bmd_line_copy["konto"]),
                    ],
                    limit=1,
                ).id
                
                bmd_line_copy["account_contra_id"] = account_obj.search(                   
                    [
                        ("company_id", "=", company.id),
                        ("code", "=", bmd_line_copy["gkto"]),
                    ],
                    limit=1,
                ).id

                bmd_line_copy["bmd_export_id"] = self.id
                line_obj.create(bmd_line_copy)

            for account_data in accounts.values():
                addExportLine(account_data)

        def exportMove(move):
            move_lines = move.line_id
            group_credit = 0.0
            group_debit = 0.0
            group_lines = []
            group = [group_lines]

            # group lines
            for line in move_lines:
                group_lines.append(line)
                if line.credit:
                    group_credit += line.credit
                else:
                    group_debit += line.debit
                # group if balanced
                if group_credit == group_debit and group_debit > 0:
                    group_lines = []
                    group.append(group_lines)

            for group_lines in group:
                debit = []
                credit = []
                reconcile_ids = []
                partner = None

                for line in group_lines:
                    if not partner:
                        partner = line.partner_id
                    #
                    if line.credit:
                        credit.append({"line": line, "amount": line.credit})
                    else:
                        debit.append({"line": line, "amount": line.debit})

                    reconcile_id = (
                        line.reconcile_id or line.reconcile_partial_id or None
                    )
                    if reconcile_id:
                        reconcile_ids.append(reconcile_id.id)

                if not debit or not credit:
                    continue

                invoice = None
                if reconcile_ids:
                    cr.execute(
                        "SELECT inv.id FROM account_invoice inv "
                        " INNER JOIN account_move_line l ON l.move_id = inv.move_id "
                        " INNER JOIN account_move_reconcile r ON (r.id IN %s) AND (r.id = l.reconcile_id OR r.id = l.reconcile_partial_id) "
                        " GROUP BY 1 ",
                        (tuple(reconcile_ids),),
                    )

                    invoice_ids = [r[0] for r in cr.fetchall()]
                    invoice = invoice_ids and invoice_obj.browse(invoice_ids[0]) or None

                    if not partner:
                        partner = invoice.partner_id

                bucod = None
                main = None
                lines = None
                sign = 1.0

                if len(debit) == 1 and not (
                    len(credit) == 1 and credit[0]["line"].name == "/"
                ):
                    bucod = "1"
                    main = debit[0]
                    lines = credit
                elif len(credit) == 1:
                    bucod = "2"
                    sign = -1.0
                    main = credit[0]
                    lines = debit
                else:
                    taskc.logw(
                        "Buchung %s kann nicht exportiert werden (mehr als eine Haben oder Soll Buchung)"
                        % move.name,
                        ref="account.move,%s" % move.id,
                    )
                    raise Warning(
                        "Buchung %s kann nicht exportiert werden (mehr als eine Haben oder Soll Buchung)"
                    )

                line = main["line"]
                bmd_line_pattern = {
                    "satzart": "0",
                    "partner_id": partner and partner.id or None,
                    "konto": line.account_id.code,
                    "account_id": line.account_id.id,
                    "buchdat": move.date,
                    "belegdat": move.date,
                    "belegnr": self._sanitize_belegnr(move.name),
                    "bucod": bucod,
                    "mwst": 0,
                    "steuer": 0.0,
                    "symbol": journal and journal.code or "",
                    "gegenbuchkz": "E",
                    "verbuchkz": "A",
                    "kost": invoice and self._sanitize_belegnr(invoice.number) or None,
                    "invoice_id": invoice and invoice.id or None,
                    "zziel": "0",
                }

                for line_data in lines:
                    line = line_data["line"]
                    bmd_line = bmd_line_pattern.copy()
                    bmd_line.update(
                        {
                            "export_id": self.id,
                            "betrag": line_data["amount"] * sign,
                            "text": line.name,
                            "gkto": line.account_id.code,
                            "account_contra_id": line.account_id.id,
                            "move_line_id": line.id,
                        }
                    )
                    line_obj.create(bmd_line)

        journals = profile.journal_ids
        if journals:
            for journal in journals:
                if journal.type in (
                    "sale",
                    "sale_refund",
                    "purchase",
                    "purchase_refund",
                ):

                    inv_domain = [
                        ("period_id", "=", period_id),
                        ("journal_id", "=", journal.id),
                        ("state", "in", ("open", "paid")),
                    ]
                    if self.number_from:
                        inv_domain.append(("number", ">=", self.number_from))

                    for invoice in invoice_obj.search(inv_domain):
                        exportInvoice(invoice)

                elif journal.type in ("bank", "cash"):

                    move_domain = [
                        ("period_id", "=", period_id),
                        ("journal_id", "=", journal.id),
                        ("state", "=", "posted"),
                    ]
                    if self.number_from:
                        move_domain.append(("name", ">=", self.number_from))
                    for move in move_obj.search(move_domain):
                        exportMove(move)

    def _create_reports(self, taskc):
        cr = self._cr
        
        invoice_obj = self.env["account.invoice"]
        account_voucher_obj = self.env["account.voucher"]
        account_bank_statement_obj = self.env["account.bank.statement"]
        account_journal_obj = self.env["account.journal"]
        account_obj = self.env["account.account"]

        profile = self.profile_id
        period = self.period_id
        company = profile.company_id
        

        period_name = period.name
        export_name = self.name

        def add_report(
            objects,
            export_name,
            title=None,
            report_name=None,
            add_pdf_attachments=False,
        ):
            if objects:
                if not report_name:
                    report_name = objects._model._name
                (report_data, report_ext, file_name) = self._renderReport(
                    report_name,
                    objects=objects,
                    add_pdf_attachments=add_pdf_attachments,
                    report_title=title,
                )

                if file_name:
                    self._export_file(
                        taskc, export_name, file_name, data=report_data
                    )
                else:
                    taskc.logw("Report *%s* not able to export" % report_name)

        # attach statement report
        if profile.send_affected_statements:
            cr.execute(
                "SELECT s.date, s.name, l.statement_id FROM bmd_export_line bl "
                " INNER JOIN account_move_line l ON l.id = bl.move_line_id "
                " INNER JOIN account_bank_statement s ON s.id = l.statement_id AND s.state = 'confirm' "
                " WHERE bl.bmd_export_id = %s "
                " GROUP BY 1,2,3 "
                " ORDER BY 1,2,3",
                (self.id,),
            )

            statements = account_bank_statement_obj.browse(
                [r[2] for r in cr.fetchall()]
            )
            add_report(
                statements,
                "affected-statements",
                title="Auszüge %s" % (export_name,),
                add_pdf_attachments=True,
            )

        if profile.send_statements:
            for journal in account_journal_obj.search([("company_id", "=", company.id)]):

                statements = account_bank_statement_obj.search(
                    [
                        ("period_id", "=", period.id),
                        ("journal_id", "=", journal.id),
                        ("state", "=", "confirm"),
                    ]
                )
                add_report(
                    statements,
                    "statements",
                    title="Auszüge %s %s" % (journal.name, export_name),
                    add_pdf_attachments=True,
                )

        # attach balance report
        if profile.send_balance_list:
            cr.execute(
                "SELECT a.code, t.account_id FROM ("
                " SELECT bl1.account_id AS account_id FROM bmd_export_line bl1 WHERE bl1.bmd_export_id = %s "
                " UNION ALL "
                " SELECT bl2.account_contra_id AS account_id FROM bmd_export_line bl2 WHERE bl2.bmd_export_id = %s "
                " ) t "
                " INNER JOIN account_account a ON a.id = t.account_id "
                " GROUP BY 1,2 "
                " ORDER BY 1,2 ",
                (self.id, self.id),
            )

            accounts = account_obj.browse([r[1] for r in cr.fetchall()])

            add_report(
                accounts,
                "statements",
                title="Saldenliste %s" % (export_name,),
                report_name="account.balance.list",
            )

        # attach voucher list
        if profile.send_voucher_list:
            vouchers = account_voucher_obj.search(
                [("period_id", "=", period.id)], order="date"
            )
            add_report(
                vouchers,
                "vouchers",
                title="Zahlungsübersicht %s" % (period_name,),
                report_name="account.voucher.list",
            )

        # attach open invoice list
        if profile.send_open_invoice_list:
            open_invoice_types = [
                ("in_invoice", "Offene Eingangsrechnungen"),
                ("out_invoice", "Offene Ausgangsrechnungen"),
            ]

            for inv_type, inv_desc in open_invoice_types:
                cr.execute(
                    "SELECT t.date_invoice, t.id FROM ( "
                    " SELECT inv.date_invoice AS date_invoice, inv.id AS id FROM account_invoice inv  "
                    "   INNER JOIN account_period p ON p.id = inv.period_id AND p.date_start <= %s "
                    "   WHERE inv.company_id = %s AND inv.state = 'open' AND inv.type = %s "
                    " UNION ALL "
                    " SELECT inv.date_invoice AS date_invoice, inv.id AS id FROM account_invoice inv "
                    "  INNER JOIN account_move_line ml ON ml.move_id = inv.move_id "
                    "  INNER JOIN account_move_reconcile r ON r.id = ml.reconcile_id "
                    "  INNER JOIN account_period p ON p.id = inv.period_id AND p.date_start <= %s "
                    "  WHERE inv.company_id = %s AND inv.state = 'paid' AND inv.type = %s AND r.create_date > %s "
                    " ) t GROUP BY 1,2 ORDER BY 1 ",
                    (
                        period.date_start,
                        company.id,
                        inv_type,
                        period.date_start,
                        company.id,
                        inv_type,
                        period.date_stop,
                    ),
                )

                invoices = invoice_obj.browse([r[1] for r in cr.fetchall()])
                add_report(
                    invoices,
                    "open-invoices",
                    title="%s %s" % (inv_desc, period_name),
                    report_name="account.invoice.list",
                )

        # attach invoice list
        invoice_reports = []
        if profile.send_invoice_list:
            invoice_reports.append(
                (
                    "account.invoice.list",
                    [
                        ("Liste Ausgangsrechnungen", "out_invoice"),
                        ("Liste Eingangsrechnungen", "in_invoice"),
                        ("Liste Kundengutschriften", "out_refund"),
                        ("Liste Lieferantengutschriften", "in_refund"),
                    ],
                )
            )
        if profile.send_invoices:
            invoice_reports.append(
                (
                    "account.invoice",
                    [
                        ("Ausgangsrechnungen", "out_invoice"),
                        ("Eingangsrechnungen", "in_invoice"),
                        ("Kundengutschriften", "out_refund"),
                        ("Lieferantengutschriften", "in_refund"),
                    ],
                )
            )

        for invoice_report, invoice_types in invoice_reports:
            for invoice_name, invoice_type in invoice_types:
                invoices = invoice_obj.search(
                    [
                        ("period_id", "=", period.id),
                        ("type", "=", invoice_type),
                        ("state", "!=", "draft"),
                        ("state", "!=", "cancel"),
                    ],
                    order="date_invoice",
                )

                valid_invoices = invoice_obj.browse()
                if invoice_type in ("in_invoice", "in_refund"):
                    for invoice in invoices:
                        if self._getReportAttachment("account.report_invoice", invoice):
                            valid_invoices |= invoice
                        else:
                            taskc.logw(
                                "Rechnung ohne Beleg",
                                ref="account.invoice,%s" % invoice.id,
                            )

                add_report(
                    valid_invoices,
                    "%s-invoices" % invoice_type,
                    title="%s %s" % (invoice_name, period_name),
                    report_name=invoice_report
                )
                
    @api.multi
    def action_send_email(self):
        self.ensure_one()
        
        attachment_ids = self.export_file_ids.mapped("attachment_id").ids
        
        wizard_form = self.env.ref("mail.email_compose_message_wizard_form")
        wizard_context = {
            "default_model": "bmd_export",
            "default_res_id": self.id,
            "default_composition_mode": "comment",
            "default_attachment_ids": attachment_ids            
        }
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(wizard_form.id, "form")],
            "view_id": wizard_form.id,
            "target": "new",
            "context": wizard_context,
        }


class BmdExportLine(models.BaseModel):
    _name = "bmd.export.line"
    _description = "BMD Export Line"
    _order = "belegnr"
    _name_rec = "belegnr"

    bmd_export_id = fields.Many2one("bmd.export", "BMD Export", index=True)
    move_line_id = fields.Many2one("account.move.line", "Buchungszeile")
    invoice_id = fields.Many2one("account.invoice", "Rechnung")
    partner_id = fields.Many2one("res.partner", "Partner")
    account_id = fields.Many2one("account.account", "Konto")
    account_contra_id = fields.Many2one("account.account", "Gegenkonto")

    satzart = fields.Selection(
        [
            ("0", "FIBU-Buchungssatz"),
            ("2", "Mehrzeiliger Buchungstext"),
            ("6", "Personenstammdaten"),
        ],
        "Satzart",
    )

    konto = fields.Char("Konto")
    buchdat = fields.Date("Buchnungsdatum")
    gkto = fields.Char("Gegenkonto")
    belegnr = fields.Char("Belegnummer")
    belegdat = fields.Date("Belegdatum")
    kost = fields.Char("Kostenstelle")
    kotraeger = fields.Integer("Kostenträger")
    komenge = fields.Float("Kosten-Menge")
    komengenr = fields.Char("Kosten-Menge-Kz")
    kovariator = fields.Float("Kosten-Variator")
    koperiode = fields.Date("Kosten-Periode")
    mwst = fields.Integer("Steuerprozentsatz")
    steuer = fields.Float("Steuer")
    steucod = fields.Selection(
        [
            ("00", "Vorsteuer oder keine Steuer"),
            ("01", "Ist-Umsatzsteuer"),
            ("03", "Soll-Umsatzsteuer (= normale Umsatzsteuer)"),
            ("07", "innergemeinschaftliche Lieferung"),
            ("08", "Einkauf innergem. Erwerb, wenn kein VSt-Abzug besteht"),
            ("09", "Einkauf innergem. Erwerb, wenn VSt-Abzug besteht"),
            ("17", "steuerfreie Bauleistung (Erlös)"),
            ("18", "Reverse Charge ohne Vorsteuer"),
            ("19", "Reverse Charge mit Vorsteuer"),
            ("28", "Einkauf Bausteuer ohne Vorsteuer"),
            ("29", "Einkauf Bausteuer normal mit Vorsteuer"),
            ("48", "Aufwand §19/1b ohne VSt-Abzug"),
            ("49", "Aufwand §19/1b mit VSt-Abzug"),
            ("57", "Umsätze §19/1c+d"),
            ("58", "Aufwand §19/d ohne VSt-Abzug"),
            ("59", "Aufwand §19/d mit VSt-Abzug"),
            ("68", "Aufwand §19/1c ohne VSt-Abzug"),
            ("69", "Aufwand §19/1c mit VSt-Abzug"),
            ("77", "Erträge sonstige Leistungen EU"),
            ("78", "Aufwände Son.Leistungen EU ohne VSt-Abzug"),
            ("79", "Aufwände Son.Leistungen EU mit VSt-Abzug"),
        ],
        "Steuer Code",
    )

    bucod = fields.Selection(
        [("1", "Soll-Buchung"), ("2", "Haben-Buchung")], "Soll/Haben"
    )

    betrag = fields.Float("Betrag",)
    ebkennz = fields.Selection([("1", "Eingangsbeleg")], "Beleg Kennzeichen")

    skonto = fields.Float("Skonto")
    opbetrag = fields.Float("OP-Betrag", help="Offene Posten - Betrag")

    periode = fields.Date("Periode",)
    text = fields.Char("Buchungstext",)
    symbol = fields.Char("Symbol",)
    extbelegnr = fields.Char("Externe Belegnummer",)
    zziel = fields.Integer("Zahlungsziel", help="Zahlungsziel in Tagen")

    menge = fields.Float("Menge",)
    gegenbuchkz = fields.Selection(
        [("E", "Einzelbuchung"), ("S", "Sammelbuchung"), ("O", "Ohne Gegenbuchung")],
        "Gegenbuchungskennzeichen",
    )

    verbuchkz = fields.Selection(
        [("A", "Verbuchung mit PR08A"), ("P", "Sammelbuchungen durch BMD")],
        "Verbuchungskennzeichen",
    )

    bereich = fields.Selection(
        [("I", "Inland"), ("EU", "EU Ausland"), ("D", "Drittland"), ("A", "Ausland")],
        "Bereich",
    )


class BmdExportProfile(models.BaseModel):
    _name = "bmd.export.profile"
    _order = "name"

    name = fields.Char("Name", required=True)

    active = fields.Boolean("Aktiv", default=True)
    version = fields.Selection(
        [("bmd55", "5.5"), ("ntcs", "NTCS")], "Version", default="bmd55"
    , required=True)

    company_id = fields.Many2one(
        "res.company",
        "Firma",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "bmd.export.profile"
        ),
    )

    partner_name_as_matchcode = fields.Boolean("Partner als Matchcode")
    cession_code = fields.Char("Zession Code")
    receipt_primary = fields.Boolean("Erlöskonto Buchungen")
    send_affected_statements = fields.Boolean("Sende betroffene Auszüge")
    send_statements = fields.Boolean("Sende alle Auszüge")
    send_balance_list = fields.Boolean("Sende Kontensalden")
    send_voucher_list = fields.Boolean("Sende Zahlungen")
    send_open_invoice_list = fields.Boolean("Sende Liste mit offenen Rechnungen")
    send_invoice_list = fields.Boolean("Sende Rechnung/Gutschriftenliste")
    send_invoices = fields.Boolean("Sende Rechnungen/Gutschriften")

    journal_ids = fields.Many2many(
        "account.journal",
        "bmd_export_profile_journal_rel",
        "profile_id",
        "journal_id",
        string="Journals",
    )
