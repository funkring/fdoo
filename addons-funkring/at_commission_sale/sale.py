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
from openerp.tools.translate import _
from at_base import util

class sale_order(osv.osv):
       
    def _calc_sale_commission(self, cr, uid, ids, context=None):
        commission_line_obj = self.pool.get("at_commission.line")
        period_obj = self.pool.get("account.period")
        pricelist_obj = self.pool.get("product.pricelist")
        pricelist_item_obj = self.pool.get("product.pricelist.item")
       
        
        period_ids = set()
        salesman_ids = set()
        
        for order in self.browse(cr, uid, ids):
            company = order.company_id 
            #
            period_ids2 = period_obj.search(cr, uid, [("date_start", "=", util.getFirstOfMonth(order.date_order))])                                
            if not period_ids2:
                raise osv.except_osv(_("Error !"),_("No Period found for creating commission line"))
            period_id = period_ids2[0] 
            #
            if company.commission_type == "order":
                for line in order.order_line:
                    if line.product_id:
                        team = order.user_id.context_section_id
                        partner = order.user_id.partner_id
                        item_id = pricelist_obj.price_get(cr,uid,[order.pricelist_id.id],line.product_id.id,line.product_uos_qty,
                                                              partner=order.partner_id.id,)["item_id"][order.pricelist_id.id]
                        
                        if partner and team:
                            percent = item_id and pricelist_item_obj.browse(cr,uid,item_id).commission or 0.0
                            
                            if not percent:
                                percent = team.sales_commission
                            
                            if percent:
                                period_ids.add(period_id)
                                salesman_ids.add(order.user_id.id)
                                #
                                commission_product = team.property_commission_product
                                journal = team.property_analytic_journal
                                amount = commission_line_obj._get_sale_commission(cr, uid, line.price_subtotal, percent)
                                #
                                values = {
                                    "order_id" : order.id,
                                    "name": _("Sales Commission: %s") % (line.name,),
                                    "date": order.date_order,
                                    "account_id": order.project_id.id,
                                    "unit_amount": line.product_uos_qty,
                                    "amount": amount,
                                    "base_commission" : percent,   
                                    "total_commission" : percent,                             
                                    "product_id": commission_product.id,
                                    "product_uom_id": commission_product.uom_id.id,
                                    "general_account_id": commission_product.account_income_standard_id.id,
                                    "journal_id": journal.id,
                                    "salesman_id" : order.user_id.id,
                                    "partner_id" : partner.id,
                                    "order_line_id" : line.id,
                                    "user_id" : uid,
                                    "ref": order.name or None,
                                    "sale_partner_id" : order.partner_id.id,
                                    "sale_product_id" : line.product_id.id,
                                    "period_id" : period_id,
                                    "price_sub" : line.price_subtotal
                                }
                                commission_line_ids = commission_line_obj.search(cr, uid, [("order_line_id", "=", line.id), ("partner_id", "=", order.user_id.partner_id.id)])
                                commission_line_id = commission_line_ids and commission_line_ids[0] or None
                                #
                                if not commission_line_id:
                                    commission_line_obj.create(cr, uid, values)
                                elif commission_line_id and not commission_line_obj.browse(cr, uid, commission_line_id).invoiced_id:
                                    commission_line_obj.write(cr, uid, commission_line_id, values)
        #    
        period_ids = list(period_ids)
        salesman_ids = list(salesman_ids)
        commission_line_obj._update_bonus(cr,uid,salesman_ids,period_ids)

    def action_wait(self, cr, uid, ids, *args):
        super(sale_order, self).action_wait(cr, uid, ids, *args)
        self._calc_sale_commission(cr, uid, ids)    
        
    def action_cancel(self, cr, uid, ids, context=None):
        ids_tuple = tuple(ids)
        
        cr.execute("SELECT l.salesman_id FROM at_commission_line l "
        " INNER JOIN sale_order_line ol ON ol.id = l.order_line_id "
        " WHERE ol.order_id IN %s "
        " GROUP BY 1", (ids_tuple,) )
        
        salesman_ids = [r[0] for r in cr.fetchall()]
        
        cr.execute("SELECT l.period_id FROM at_commission_line l "
        " INNER JOIN sale_order_line ol ON ol.id = l.order_line_id "
        " WHERE ol.order_id IN %s "
        " GROUP BY 1", (ids_tuple,) )
        
        period_ids = [r[0] for r in cr.fetchall()]
        
        res = super(sale_order,self).action_cancel(cr,uid,ids,context)
        commission_line_obj = self.pool.get("at_commission.line")
        commission_line_obj._update_bonus(cr,uid,salesman_ids,period_ids,context=context)
        return res
        
    _inherit = "sale.order"
sale_order()