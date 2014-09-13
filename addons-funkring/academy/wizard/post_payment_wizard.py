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

class post_payment_wizard(osv.TransientModel):
    
    def action_post_payment(self, cr, uid, ids, context=None):
        # get objects
        wizard = self.browse(cr, uid, ids[0], context=context)
        reg_inv_obj = self.pool["academy.registration.invoice"]
        invoice_obj = self.pool["account.invoice"]
        payment_obj = self.pool["academy.payment"]        
        payment_ids = util.active_ids(context,payment_obj)
        
        # process payments
        for payment in payment_obj.browse(cr, uid, payment_ids, context=context):
            if payment.invoice_id:
                continue
            
            semester = payment.semester_id
            reg = payment.reg_id
            
            reg_inv_id = reg_inv_obj.search_id(cr, uid, [("registration_id","=",reg.id),("semester_id","=",semester.id)])
            if not reg_inv_id:
                continue

            # get invocie            
            invoice = reg_inv_obj.browse(cr, uid, reg_inv_id, context=context).invoice_id
            if invoice.state not in ("draft","cancel") and invoice.residual and invoice.residual >= payment.amount:
                # do payment
                res = invoice_obj._create_payment(cr, uid, invoice.id, wizard.journal_id.id,
                                            amount=payment.amount,
                                            date=payment.date,
                                            post=True, 
                                            context=context)
                
                # check if everything ok, and add invoice
                # to payment
                voucher_id = res.get("voucher_id")
                if voucher_id:
                    payment_obj.write(cr, uid, [payment.id], 
                                      {"invoice_id" : invoice.id,
                                       "voucher_id" : voucher_id },
                                       context=context)
                    
        return { "type" : "ir.actions.act_window_close" }
                                
            
            
            
    _name = "academy.post.payment.wizard"
    _description = "Post Payment"
    _columns =  {
        "journal_id" : fields.many2one("account.journal","Journal",required=True)    
    }
    _defaults = {
      "journal_id" : lambda self, cr, uid, context: self.pool["account.journal"].search_id(cr, uid, [("type","=","bank")], context=context)
    }

    