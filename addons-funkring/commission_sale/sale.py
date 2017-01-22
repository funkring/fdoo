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
        
    def _calc_sale_commission(self, cr, uid, ids, context=None):
        commission_line_obj = self.pool.get("commission.line")
        
        period_ids = set()
        salesman_ids = set()
        
        for order in self.browse(cr, uid, ids, context=context):
            company = order.company_id 
            analytic_account = order.project_id
            if company.commission_type == "order" and analytic_account:
                for line in order.order_line:
                    product = line.product_id
                    if product:      
                        commission_lines = commission_line_obj._get_sale_commission(cr, uid, 
                                                                 line.name, order.user_id, 
                                                                 order.partner_id, 
                                                                 product, 
                                                                 line.product_uos_qty, 
                                                                 line.price_subtotal, 
                                                                 date=order.date_order, 
                                                                 pricelist=order.pricelist_id, 
                                                                 defaults={
                                                                    "ref": order.name,
                                                                    "order_line_id" : line.id,
                                                                    "order_id" : order.id,
                                                                    "account_id": analytic_account.id,
                                                                    "sale_partner_id" : order.partner_id.id,
                                                                    "sale_product_id" : line.product_id.id
                                                                 }, context=context)
                        
                        for commisson_line in commission_lines:
                            period_ids.add(commisson_line["period_id"])
                            salesman_ids.add(commisson_line["partner_id"])
                            
                            commission_line_id = commission_line_obj.search_id(cr, uid, [("order_line_id", "=", commisson_line["order_line_id"]),
                                                                                       ("partner_id", "=", commisson_line["partner_id"]),
                                                                                       ("product_id","=", commisson_line["product_id"])], context=context)
                            if commission_line_id:
                                commission_line_obj.write(cr, uid, commission_line_id, commisson_line, context=context)                                
                            else:
                                commission_line_obj.create(cr, uid, commisson_line, context=context)

        # update bonus        
        period_ids = list(period_ids)
        salesman_ids = list(salesman_ids)
        commission_line_obj._update_bonus(cr, uid, salesman_ids, period_ids, context=context)

    _inherit = "sale.order"
