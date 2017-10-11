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
from openerp.addons.at_base import util

import csv
import base64
import StringIO
import re

import logging
import datetime
_logger = logging.getLogger(__name__)

class bmd_reconcile_wizard(models.TransientModel):
    _name = "bmd.reconcile.wizard"
    _description = "Reconcile Wizard"
    
    company_id = fields.Many2one("res.company","Firma",
                                 default=lambda self: self.env['res.company']._company_default_get('bmd.reconcile.wizard'))
    
    journal_id = fields.Many2one("account.journal","Journal", required=True)
    exclude = fields.Char("Ignoriere Kennzeichen", help="Ignoriere Kennzeigen beim Import mit Beistrich getrennt")
    csv = fields.Binary("Offene Postenliste (CSV)", required=True)
    
    
    @api.multi
    def action_reconcile(self):
        wizard = self.ensure_one()

        csv_data = base64.decodestring(wizard.csv)
        cvs_data = unicode(csv_data,"iso8859-15").encode("UTF-8")
        csv_data = StringIO.StringIO(csv_data)                
        
        date = None
        open_date = None
        date_pattern = re.compile("per ([0-9]{1,2})\\. (\w+) ([0-9]{4})")        
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
        
        reader = csv.reader(csv_data,delimiter=';',quotechar=None)
        fields = {
            "Kto-Nr": None,
            "Rng-Nr": None,
            "Rng-Betrag": None,
            "OP-Betrag": None,
            "Text": None,
            "BS": None,
            "Rng-Dat": None
        }

        initialized = False
        last_col = 0
        row_n = 0
        
        numbers = []
        invoice_obj = self.env["account.invoice"]
        
        exclude = wizard.exclude or ""
        exclude = set(exclude.split(","))
                 
        def parseStr(val):
            if not val:
                return ""
            if not isinstance(val,basestring):
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
                        found+=1
                                     
                initialized = (found == len(fields))
                    
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
                  invoice_date = datetime.datetime.strptime(invoice_date,"%y/%m/%d").strftime("%Y-%m-%d")
                  if invoice_date:
                    if not open_date:
                      open_date = invoice_date
                    else:
                      open_date = max(invoice_date, open_date)
                
                #partner_ref = parseStr(row[fields["Kto-Nr"]])
                #amount = parseFloat(row[fields["Rng-Betrag"]])
                #balance =  parseFloat(row[fields["OP-Betrag"]])
                
        
        if date and open_date:
          date = min(date, util.getNextDayDate(open_date))
        
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
            check_domain = [("company_id","=",company_id),("type","=",inv_type),("number","in",numbers)]
            found_invoice_count = invoice_obj.search(check_domain, count=True)
            if found_invoice_count != len(numbers):
                found_invoice_vals = invoice_obj.search_read(check_domain, ["number"])
                found_invoice_numbers = set([v["number"] for v in found_invoice_vals])
                not_found_numbers = list(set(numbers).difference(found_invoice_numbers))
                like_found_numbers = set()
                for notfound_num in not_found_numbers:
                  notfound_vals = invoice_obj.search_read([("number","like",notfound_num)],["number"])
                  for notfound_val in notfound_vals:
                    numbers.append(notfound_val["number"])
                    like_found_numbers.add(notfound_num)
                  
                not_found_numbers = list(set(not_found_numbers) - like_found_numbers)
                if not_found_numbers:
                  raise Warning("Es konnten nicht alle Rechnungen gefunden werden:\n %s" % ", ".join(not_found_numbers))
            
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
        