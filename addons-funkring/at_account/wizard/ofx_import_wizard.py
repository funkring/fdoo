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
from openerp.addons.at_base import util
from openerp.osv.fields import datetime as datetime_field
from ofxparse import OfxParser
import base64

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class ofx_import_wizard(osv.TransientModel):

    _name = "account.ofx.import.wizard"
    _description = "OFX Import Wizard"
    _columns = {
        "ofx_datas" : fields.binary("OFX Data", required=True)
    }
    
    def _import_ofx(self, cr, uid, wizard, context=None):        
        statement_obj = self.pool["account.bank.statement"]
        line_obj = self.pool["account.bank.statement.line"]
        
        stat_id = util.active_ids(context, "account.bank.statement")
        if not stat_id:
            return False
          
        stat = statement_obj.browse(cr, uid, stat_id, context=context)
        
        datas = wizard.ofx_datas
        if not datas:
            return False
          
        datab = base64.decodestring(datas)
        if not datab:
            return False
        
        if stat.state != "draft":
            return False
        
        fp =  StringIO(datab)
        ofx = OfxParser.parse(fp)
        if not ofx:
            return False
        
        for account in ofx.accounts:
            statement = account.statement
            statement_date = util.dateToStr(statement.start_date)
            balance_end = statement.balance
            balance_start = balance_end
                    
            lines = []
            for trans in statement.transactions:
                trans_date = datetime_field.context_timestamp(cr, uid,
                                            timestamp=trans.date,
                                            context=context)
                
                balance_start-=trans.amount
                line = (0,0, {
                    "sequence" : len(lines)+1,
                    "name" : trans.memo,
                    "date" : util.dateToStr(trans_date),
                    "ref" : trans.id,                         
                    "amount" : float(trans.amount)
                })
                lines.append(line)
                
            
            values = {}
            # change journal
            journal_id = stat.journal_id.id
            onchange_values = statement_obj.onchange_journal_id(cr, uid, [], journal_id).get("value")
            if onchange_values:
                values.update(onchange_values)
            # change date
            onchange_values = statement_obj.onchange_date(cr, uid, [], statement_date, values.get("company_id")).get("value")
            if onchange_values:
                values.update(onchange_values)    
            
            values.update({
                "date" : statement_date,
                "journal_id": journal_id,
                "balance_end_real" : float(balance_end),
                "balance_start" : float(balance_start),
                "line_ids" : lines
            })

            # remove old lines                
            line_ids = line_obj.search(cr, uid, [("statement_id","=",stat.id)])
            if line_ids:
                line_obj.unlink(cr, uid, line_ids)
            
            # update statement
            statement_id = statement_obj.write(cr, uid, [stat.id], values, context=context)                
        
        return True
   
    def action_import(self, cr, uid, ids, context=None):
        for wizard in self.browse(cr, uid, ids, context=context):
            self._import_ofx(cr, uid, wizard, context=context)
            return True
    