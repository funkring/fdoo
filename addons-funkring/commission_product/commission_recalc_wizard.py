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

from openerp.osv import fields, osv

class commission_recalc_wizard(osv.osv_memory):
    
    def do_recalc(self, cr, uid, ids, context=None):
        res = super(commission_recalc_wizard, self).do_recalc(cr, uid, ids, context)
        invoice_obj = self.pool.get("account.invoice")
        order_obj = self.pool.get("sale.order")
        for wizard in self.browse(cr, uid, ids):
            if wizard.date_from and wizard.date_to:
                order_ids = order_obj.search(cr, uid, [("state", "!=", "draft"), ("state", "!=", "cancel"), 
                                                           ("date_order", ">=", wizard.date_from), ("date_order", "<=", wizard.date_to)])
                invoice_ids = invoice_obj.search(cr, uid, [("state", "!=", "draft"), ("state", "!=", "cancel"), 
                                                           ("date_invoice", ">=", wizard.date_from), ("date_invoice", "<=", wizard.date_to)])
                
            elif not wizard.date_from and not wizard.date_to:
                order_ids = order_obj.search(cr, uid, [("state", "!=", "draft"), ("state", "!=", "cancel")])
                invoice_ids = invoice_obj.search(cr, uid, [("state", "!=", "draft"), ("state", "!=", "cancel")])
                
            elif not wizard.date_from and wizard.date_to:
                order_ids = order_obj.search(cr, uid, [("state", "!=", "draft"), ("state", "!=", "cancel"), ("date_order", "<=", wizard.date_to)])
                invoice_ids = invoice_obj.search(cr, uid, [("state", "!=", "draft"), ("state", "!=", "cancel"), ("date_invoice", "<=", wizard.date_to)])
            
            else:
                order_ids = order_obj.search(cr, uid, [("state", "!=", "draft"), ("state", "!=", "cancel"), ("date_order", ">=", wizard.date_from)])
                invoice_ids = invoice_obj.search(cr, uid, [("state", "!=", "draft"), ("state", "!=", "cancel"), ("date_invoice", ">=", wizard.date_from)])
                
        order_obj._calc_product_commission(cr, uid, order_ids, context)
        invoice_obj._calc_product_commission(cr, uid, invoice_ids, context)
        return res
    
    _inherit = "commission.recalc_wizard"
