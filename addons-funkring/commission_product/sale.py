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

from openerp.osv import osv

    
class sale_order_line(osv.osv):    
    _inherit = "sale.order.line"
        
    def _product_margin_extra(self, cr, uid, line, context=None):
        res = super(sale_order_line, self)._product_margin_extra(cr, uid, line, context=context)
        product = line.product_id        
        commission_obj = self.pool["commission.line"]
        
        if product:
            order = line.order_id
            commissionEntries = commission_obj._get_product_commission(cr, uid, 
                                      line.name, 
                                      product,
                                      line.product_uos_qty, 
                                      line.price_subtotal, 
                                      order.date_order,
                                      obj=line,
                                      company=order.company_id,
                                      context=context)
                        
            for commissionEntry in commissionEntries:
                res+=commissionEntry["amount"]
        return res
