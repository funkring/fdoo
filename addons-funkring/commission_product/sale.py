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
from openerp.tools.translate import _
from openerp.addons.at_base import util

class sale_order(osv.osv):
      
    def _calc_product_commission(self, cr, uid, ids, force=False, context=None):
        commission_obj = self.pool.get("commission_product.commission")
        commission_line_obj = self.pool.get("commission.line")
        for order in self.browse(cr, uid, ids, context=context):
            company = order.company_id 
            analytic_account = order.project_id
            if company.commission_type == "order" and analytic_account:
                for line in order.order_line:
                    if line.product_id:
                        commission_lines = commission_line_obj._get_product_commission(cr, uid, 
                                                     line.name, 
                                                     line.product_id, 
                                                     line.product_uos_qty, 
                                                     line.price_subtotal, 
                                                     order.date_order,
                                                     defaults= {
                                                        "account_id": analytic_account.id,
                                                        "order_line_id" : line.id,
                                                        "ref": order.name,
                                                        "sale_partner_id" : order.partner_id.id,
                                                        "sale_product_id" : line.product_id.id
                                                     },
                                                     context=context)  
                        
                        for commission_line in commission_lines:
                            commission_line_id = commission_line_obj.search_id(cr, uid, [("order_line_id", "=", line.id), 
                                                                                         ("product_id", "=", commission_line["product_id"]),
                                                                                         ("partner_id", "=", commission_line["partner_id"])])
                            if commission_line_id:
                                commission_line_obj.write(cr, uid, commission_line_id, commission_line, context=context)
                            else:
                                commission_line_obj.create(cr, uid, commission_line, context=context)
        return True
    
    _inherit = "sale.order"
    
    
class sale_order_line(osv.osv):    
    _inherit = "sale.order.line"
        
    def _product_margin_extra(self, cr, uid, line, context=None):
        res = super(sale_order_line, self)._product_margin_extra(cr, uid, line, context=context)
        product = line.product_id        
        if product:
            order = line.order_id
            commissionEntries = self.pool("commission.line")._get_product_commission(cr, uid, 
                                      line.name, 
                                      product,
                                      line.product_uos_qty, 
                                      line.price_subtotal, 
                                      order.date_order,
                                      context=context)
                        
            for commissionEntry in commissionEntries:
                res+=commissionEntry["amount"]
        return res
