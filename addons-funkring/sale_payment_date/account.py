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

from at_base import util
from openerp.osv import fields, osv

from openerp.tools.translate import _

class account_invoice(osv.osv):
    
    def onchange_payment_term_date_invoice(self, cr, uid, ids, payment_term_id, date_invoice):        
        date_payment = None
        #search payment date
        invoice_id = util.idFirst(ids)
        if invoice_id:
            #browse with admin right to prevent access rules fail
            invoice = self.browse(cr, 1, invoice_id)
            date_payment = None
            for order in invoice.sale_order_ids:
                order_payment_date = order.payment_date
                if order_payment_date:
                    if not date_payment:
                        date_payment = order_payment_date
                    else:
                        date_payment = min(date_payment,order_payment_date)
        
        #no payment term
        if not payment_term_id:
            if date_payment:
                return {'value':{'date_due': date_payment}}
            return {}
        
        res = {}
        pt_obj = self.pool.get('account.payment.term')
        if not date_invoice:
            date_invoice = util.currentDate()
        if date_payment:
            date_invoice=date_payment
                
        #compute date as usual        
        pterm_list = pt_obj.compute(cr, uid, payment_term_id, value=1, date_ref=date_invoice)
        if pterm_list:
            pterm_list = [line[0] for line in pterm_list]
            pterm_list.sort()
            res = {'value':{'date_due': pterm_list[-1]}}
        else:
            raise osv.except_osv(_('Data Insufficient !'), _('The Payment Term of Supplier does not have Payment Term Lines(Computation) defined !'))
        return res
    
    def _payment_date(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for invoice in self.browse(cr, uid, ids):
            min_date = None
            for order in invoice.sale_order_ids:
                if order.payment_date:
                    if min_date:
                        min_date = min(min_date,order.payment_date)
                    else:
                        min_date = order.payment_date
            res[invoice.id] = min_date
        return res
        
    
    
    _inherit = "account.invoice"
    
    _columns = {
        "payment_date" : fields.function(_payment_date, type="date", string="Payment date", method=True)
    }
    
    
    
    
    
account_invoice()