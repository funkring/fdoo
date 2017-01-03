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
from openerp import SUPERUSER_ID
from datetime import datetime

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        "invoice_text" : fields.text("Sale Invoice Text"),
        "invoice_in_text" : fields.text("Purchase Invoice Text"),
        "refund_text" : fields.text("Customer Refund Text"),
        "refund_in_text" : fields.text("Supplier Refund Text"),
        "code" : fields.char("Code"),
        "fiscal_auto_year" : fields.boolean("Auto fiscal year"),
        "fiscal_auto_seq" : fields.boolean("Auto fiscal year sequence")
    }
    _defaults = {
        "fiscal_auto_year" : True,
        "fiscal_auto_seq" : True
    }
    
    def create_fiscalyear(self, cr, uid, ids, year, context=None):
        if not ids:
            return True
        
        fiscalyear_obj = self.pool["account.fiscalyear"]
        journal_obj = self.pool["account.journal"]
        sequence_obj = self.pool["ir.sequence"]
        fiscal_sequence_obj = self.pool["account.sequence.fiscalyear"]
        
        # end/start date
        date_start = year+"-01-01"
        date_end = year+"-12-31"
        short_year = year[2:] 
        
        # eval prefix
        def evalStr(str):
            if str:
                return str.replace("%(year)s", year).replace("%(y)s",short_year)
            return str
        
        # create fiscal year
        for company in self.browse(cr, uid, ids, context=context):
            # fiscal year
            fiscalyear_ids = fiscalyear_obj.search(cr, SUPERUSER_ID, [("company_id","=",company.id),("date_start","<=",date_start),("date_stop",">=",date_end)], context=context)
            if fiscalyear_ids:
                continue
            
            # create fiscal year
            fiscalyear_id = fiscalyear_obj.create(cr, uid, {
                "name" : year,
                "code" : year,
                "company_id" : company.id,
                "date_start" : date_start,
                "date_stop" : date_end
            }, context=context)
            fiscalyear_ids = [fiscalyear_id]
            
            # create periods
            fiscalyear_obj.create_period(cr, uid, fiscalyear_ids, context=context)
            
            # check if fiscal sequence should created
            if not company.fiscal_auto_seq:
                continue
            
            journal_ids = journal_obj.search(cr, uid, [("company_id","=",company.id),("type","in",["sale","sale_refund","purchase","purchase_refund"])], context=context)
            for journal in journal_obj.browse(cr, uid, journal_ids, context=context):
                sequence = journal.sequence_id
                # check if already exist
                fiscalyear_sequence_ids = fiscal_sequence_obj.search(cr, uid, [("sequence_main_id","=",sequence.id),("fiscalyear_id","=",fiscalyear_id)], context=context)
                if fiscalyear_sequence_ids:
                    continue
                
                # create fiscal year sequence
                name = " ".join((sequence.name,year))                    
                prefix = evalStr(sequence.prefix) 
                suffix = evalStr(sequence.suffix)
                new_sequence_id = sequence_obj.create(cr, uid, {
                    "name": name,                    
                    "prefix": prefix,
                    "suffix": suffix,
                    "padding": sequence.padding,
                    "number_increment": sequence.number_increment,
                    "implementation": sequence.implementation,
                    "company_id": company.id
                })
                
                # assign 
                fiscal_sequence_obj.create(cr, uid, {
                    "sequence_main_id" : sequence.id,
                    "sequence_id" : new_sequence_id,
                    "fiscalyear_id" :  fiscalyear_id                
                }, context=context)
            
        return True
    
    def auto_fiscal_year(self, cr, uid, context=None):        
        company_ids = self.search(cr, uid, [("fiscal_auto_year","=",True)], context=context)
        if company_ids:
            year = datetime.now().year        
            years = [str(year),str(year+1)]
            for year in years:
                self.create_fiscalyear(cr, uid, company_ids, context=context)
        
