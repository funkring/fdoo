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

from openerp import models, fields, api, _
from openerp.exceptions import Warning

import csv
import base64
import StringIO
import re

import logging
_logger = logging.getLogger(__name__)

class bmd_reconcile_wizard(models.TransientModel):
    _name = "bmd.reconcile.wizard"
    _description = "Reconcile Wizard"
    
    company_id = fields.Many2one("res.company","Firma",
                                 default=lambda self: self.env['res.company']._company_default_get('bmd.reconcile.wizard'))
    
    journal_id = fields.Many2one("account.journal","Journal", required=True)
    csv = fields.Binary("Offene Postenliste (CSV)", required=True)
    
    
    @api.multi
    def action_reconcile(self):
        wizard = self.ensure_one()

        csv_data = base64.decodestring(wizard.csv)
        cvs_data = csv_data.decode("iso8859-15")
        csv_data = csv_data.encode("UTF-8")
        csv_data = StringIO.StringIO(csv_data)                
        
        date = None
        date_pattern = re.compile("per ([0-9]{1,2})\\. ([A-Za-z]+) ([0-9]{4})")        
        month_dict = {
            "Jänner":   "01",
            "Februar":  "02",
            "März":     "03",
            "April":    "04",
            "Mai":      "05",
            "Juni":     "06",
            "Juli":     "07",
            "August":   "08",
            "September":"09",
            "Oktober":  "10",
            "November": "11",
            "Dezember": "12" 
        }
        
        reader = csv.reader(csv_data,delimiter=',',quotechar=None)
        
        fields = {
            "Kto-Nr": None,
            "Rng-Nr": None,
            "Rng-Betrag": None,
            "OP-Betrag" :None
        }

        initialized = False
        last_col = 0
        row_n = 0
        
        numbers = []
        invoice_obj = self.env["account.invoice"]
                 
        def parseStr(val):
            if not val:
                return ""
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
                        found+=1
                                     
                initialized = (found == len(fields))
                    
            else:
                
                if len(row) <= last_col or not row[0] or not row[0].strip():
                    continue
                
                number = parseStr(row[fields["Rng-Nr"]])
                if not number:
                    Warning("Rechnungsnummer in Zeile %s ist leer" % row_n)
                    
                numbers.append(number)
                
                #partner_ref = parseStr(row[fields["Kto-Nr"]])
                #amount = parseFloat(row[fields["Rng-Betrag"]])
                #balance =  parseFloat(row[fields["OP-Betrag"]])
                
        
        if not date:
            raise Warning("Es wurde kein Datum gefunden!")
        if not initialized:
            raise Warning("Es wurden keine Daten gefunden!")
        
        inv_type = "out_invoice"
        company_id = wizard.company_id.id
        journal_id = wizard.journal_id.id
        
        # check invoices
        domain = [("company_id","=",company_id),("date_invoice","<",date),("type","=",inv_type),("state","=","open")]
        if numbers:
            domain.append(("number","not in",numbers))
            found_invoice_count = invoice_obj.search([("company_id","=",company_id),("date_invoice","<",date),("type","=",inv_type),("number","in",numbers)], count=True)
            if found_invoice_count != len(numbers):
                raise Warning("Es konnten nicht alle Rechnungen gefunden werden")
            
            _logger.info("found open invoices %s" % found_invoice_count)
            
        # reconcile invoices
        voucher_obj = self.pool["account.voucher"]
        partner_obj = self.env["res.partner"]
        
        for inv in invoice_obj.search(domain, order="date_invoice desc"):
           
            if not inv.account_id.reconcile:
                inv.account_id.reconcile = True
            
            try:
                _logger.info("reconcile invoice %s" % inv.number)
                res = inv.invoice_pay_customer()
                
                voucher_ctx = dict(self._context)
                voucher_ctx.update(res["context"])
                
                partner_id = voucher_ctx["default_partner_id"]
                amount = voucher_ctx["default_amount"]
                voucher_type = voucher_ctx["type"]
                
                res = voucher_obj.onchange_journal_voucher(self._cr, self._uid, [],
                                                    partner_id=partner_id,
                                                    price=amount,
                                                    journal_id=journal_id,
                                                    ttype=voucher_type,
                                                    company_id = company_id,
                                                    context=voucher_ctx)
                
                        
                values = res["value"]
                values["journal_id"] = journal_id
                
                def conv_ids(name):                
                    if name in values:
                        values[name] = [(0,0,v) for v in values[name]]
                   
                conv_ids("line_cr_ids")
                conv_ids("line_dr_ids")     
                                    
                voucher_id = voucher_obj.create(self._cr, self._uid, values, context=voucher_ctx)
                voucher_obj.button_proforma_voucher(self._cr, self._uid, [voucher_id], context=voucher_ctx)
                
                
                self._cr.commit()
            except Exception as e:
                raise Warning("Fehler bei Rechnung %s:%s" % (inv.number, str(e))) 
                
        
        return True
        