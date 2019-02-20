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
          order_domain = [("state", "not in", ["draft","cancel","sent"])]
          invoice_domain = [("state", "!=", "draft"),("state", "!=", "cancel")]
        
          if wizard.user_id:
            partner_id = wizard.user_id.partner_id.id
            invoice_domain.append(("invoice_line.product_id.commission_ids.partner_id","=",partner_id))
            order_domain.append(("order_line.product_id.commission_ids.partner_id","=",partner_id))
                           
          if wizard.date_from: 
            order_domain.append(("date_order", ">=", wizard.date_from))
            invoice_domain.append(("date_invoice", ">=", wizard.date_from))
            
          if wizard.date_to:
            order_domain.append(("date_order", "<=", wizard.date_to))              
            invoice_domain.append(("date_invoice", "<=", wizard.date_to))
                 
          # search
          order_ids = order_obj.search(cr, uid, order_domain)
          invoice_ids = invoice_obj.search(cr, uid, invoice_domain)
          
          # recalc
          order_obj._calc_product_commission(cr, uid, order_ids, force=True, context=context)
          invoice_obj._calc_product_commission(cr, uid, invoice_ids, force=True, context=context)
          
        return res
    
    _inherit = "commission.recalc_wizard"
