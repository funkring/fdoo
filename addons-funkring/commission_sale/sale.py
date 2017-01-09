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
        period_obj = self.pool.get("account.period")
        pricelist_obj = self.pool.get("product.pricelist")
        pricelist_item_obj = self.pool.get("product.pricelist.item")
        rule_obj = self.pool.get("commission_sale.rule")
        
        period_ids = set()
        salesman_ids = set()
        
        for order in self.browse(cr, uid, ids, context=context):
            company = order.company_id 
            #
            period_ids2 = period_obj.search(cr, uid, [("date_start", "=", util.getFirstOfMonth(order.date_order))])                                
            if not period_ids2:
                raise osv.except_osv(_("Warning!"),_("No Period found for creating commission line"))
            period_id = period_ids2[0] 
            pricelist_id = order.pricelist_id.id
            #
            if company.commission_type == "order":
                for line in order.order_line:
                    product = line.product_id
                    if product:                        
                        team = order.user_id.default_section_id
                        partner = order.user_id.partner_id
                        if partner and team:
                            # get global commission
                            percent = product.commission_percent or product.categ_id.commission_percent or team.sales_commission
                            # search for rule                                                               
                            rule = rule_obj._get_rule(cr, uid, team, product, context=context)
                            if rule:
                                percent = rule.get("commission",0.0) or 0.0
                            else:
                                # search for pricelist rule
                                item_id = pricelist_obj.price_rule_get(cr, uid, [pricelist_id], product.id, line.product_uom_qty,
                                                    partner=order.partner_id.id,context=context)[pricelist_id][1]
                                
                                if item_id:
                                    prule = pricelist_item_obj.read(cr, uid, item_id, ["commission_active","commission"], context=context)
                                    if prule.get("commission_active"):
                                        percent = prule.get("commission",0.0) or 0.0         
                            
                            if percent:
                                period_ids.add(period_id)
                                salesman_ids.add(order.user_id.id)
                                #
                                commission_product = team.property_commission_product
                                journal = team.property_analytic_journal
                                amount = commission_line_obj._get_sale_commission(cr, uid, line.price_subtotal, percent)
                                values = {
                                    "order_id" : order.id,
                                    "name": _("Sales Commission: %s") % commission_line_obj._short_name(line.name),
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
                                    "sale_product_id" : product.id,
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

    def action_wait(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_wait(cr, uid, ids, context=context)
        self._calc_sale_commission(cr, uid, ids, context=context)
        return res    
        
    def action_cancel(self, cr, uid, ids, context=None):
        ids_tuple = tuple(ids)
        
        cr.execute("SELECT l.salesman_id FROM commission_line l "
        " INNER JOIN sale_order_line ol ON ol.id = l.order_line_id "
        " WHERE ol.order_id IN %s "
        " GROUP BY 1", (ids_tuple,) )
        
        salesman_ids = [r[0] for r in cr.fetchall()]
        
        cr.execute("SELECT l.period_id FROM commission_line l "
        " INNER JOIN sale_order_line ol ON ol.id = l.order_line_id "
        " WHERE ol.order_id IN %s "
        " GROUP BY 1", (ids_tuple,) )
        
        period_ids = [r[0] for r in cr.fetchall()]
        
        res = super(sale_order,self).action_cancel(cr, uid, ids, context=context)
        commission_line_obj = self.pool.get("commission.line")
        commission_line_obj._update_bonus(cr, uid, salesman_ids, period_ids, context=context)
        return res
        
    _inherit = "sale.order"
