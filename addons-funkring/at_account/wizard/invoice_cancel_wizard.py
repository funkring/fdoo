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

from openerp.osv import osv
from openerp.addons.at_base import util

class invoice_cancel_wizard(osv.TransientModel):
    
    def action_cancel(self, cr, uid, ids, context=None):
        invoice_ids = util.active_ids(context,"account.invoice")
        invoice_obj = self.pool["account.invoice"]
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, context=context):   
            invoice_obj._cancel_invoice_all(cr, uid, invoice, context=context)             
        return { "type" : "ir.actions.act_window_close" }
        
    
    _name = "invoice.cancel.wizard"
    _description = "Invoice Cancel Wizard"
    _columns = {}
