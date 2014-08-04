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

class account_invoice(osv.osv):
    _inherit="account.invoice"
    
    def _get_next_invoice(self, cr, uid, ids, field_name, args, context=None):
        
        res = dict.fromkeys(ids)
        subscription_obj = self.pool.get("subscription.subscription")
        dates = []
        
        for invoice_id in ids:
            subscription_ids = subscription_obj.search(cr, uid, [("doc_source","=","account.invoice,"+str(invoice_id))])
            
            if subscription_ids:
                for subscription in subscription_obj.browse(cr, uid, subscription_ids):
                    dates.append(subscription.cron_id.nextcall)
                
                res[invoice_id] = min(dates)
                
        return res
    
    _columns = {
        "next_invoice" : fields.function(_get_next_invoice, type="datetime", obj="ir.cron", method=True, string="Next Invoice")
    }
    
