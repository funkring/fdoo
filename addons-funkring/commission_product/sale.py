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
    
    def _calc_product_commission(self, cr, uid, ids, context=None):
        commission_obj = self.pool.get("commission_product.commission")
        commission_line_obj = self.pool.get("commission.line")
        period_obj = self.pool.get("account.period")
        for order in self.browse(cr, uid, ids, context=context):
            company = order.company_id 
            if company.commission_type == "order":
                for line in order.order_line:
                    if line.product_id:
                        commission_ids = commission_obj.search(cr, uid, [("product_id", "=", line.product_id.id)])
                        if commission_ids:
                            for commission in commission_obj.browse(cr, uid, commission_ids):
                                factor = commission.commission_percent / 100.0
                                period = period_obj.search(cr, uid, [("date_start", "=", util.getFirstOfMonth(order.date_order))])
                                if not period:
                                    raise osv.except_osv(_('Warning!'),_("No Period found for creating commission line"))
                                                                
                                if commission.commission_percent:
                                    values = {
                                        "name": _("Product Commission: %s") % commission_line_obj._short_name(line.name),
                                        "date": order.date_order,
                                        "account_id": order.project_id.id,
                                        "unit_amount": line.product_uos_qty,
                                        "amount": line.price_subtotal*factor,
                                        "base_commission" : commission.commission_percent,
                                        "total_commission" : commission.commission_percent,
                                        "product_id": commission.property_commission_product.id,
                                        "product_uom_id": commission.property_commission_product.uom_id.id,
                                        "general_account_id": commission.property_commission_product.account_income_standard_id.id,
                                        "journal_id": commission.property_analytic_journal.id,
                                        "partner_id" : commission.partner_id.id,
                                        "order_line_id" : line.id,
                                        "user_id" : uid,
                                        "order_id" : order.id,
                                        "ref": order.name,
                                        "sale_partner_id" : order.partner_id.id,
                                        "sale_product_id" : line.product_id.id,
                                        "period_id" : period[0],
                                        "price_sub" : line.price_subtotal
                                    }
                                    
                                    commission_line_ids = commission_line_obj.search(cr, uid, [("order_line_id", "=", line.id), ("partner_id", "=", commission.partner_id.id)])
                                    commission_line_id = commission_line_ids and commission_line_ids[0] or None
                                    #
                                    if not commission_line_id:
                                        commission_line_obj.create(cr, uid, values)
                                    elif commission_line_id and not commission_line_obj.browse(cr, uid, commission_line_id).invoiced_id:
                                        commission_line_obj.write(cr, uid, commission_line_id, values)    
    
    def action_wait(self, cr, uid, ids, context=None): 
        """called when orders are confirmed"""
        res = super(sale_order, self).action_wait(cr, uid, ids, context=context)
        self._calc_product_commission(cr, uid, ids, context=context)
        return res
    
    _inherit = "sale.order"
