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
        
    def _calc_sale_commission(self, cr, uid, ids, force=False, context=None):
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
                                                                    "order_line_id": line.id,
                                                                    "account_id": analytic_account.id,
                                                                    "sale_partner_id": order.partner_id.id,
                                                                    "sale_product_id": line.product_id.id
                                                                 }, 
                                                                 commission_custom=line.commission_custom or None,                    
                                                                 context=context)
                        
                        for commisson_line in commission_lines:
                            period_ids.add(commisson_line["period_id"])
                            salesman_ids.add(commisson_line["salesman_id"])
                            
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
    
    
class sale_order_line(osv.osv):    
    _inherit = "sale.order.line"
    
    def _commission_fields(self, cr, uid, ids, field_names, arg, context=None):
      res = dict.fromkeys(ids)
      commission_line_obj = self.pool("commission.line")
      
      for line in self.browse(cr, uid, ids, context):
        
        commission_amount = 0.0
        commission = 0.0
        commission_total = 0.0
        
        if line.product_id:
          order = line.order_id
          product = line.product_id
          
          # calc without commission custom
          commissions = commission_line_obj._get_sale_commission(cr, uid, 
                                   line.name, 
                                   order.user_id, 
                                   order.partner_id, 
                                   product, 
                                   line.product_uos_qty, 
                                   line.price_subtotal, 
                                   date=order.date_order, 
                                   pricelist=order.pricelist_id, 
                                   context=context)
          
          for c in commissions:
            commission_amount += c["amount"]
            commission += c["total_commission"]
            
          # calc with commission custom
          commission_total = commission
          if line.commission_custom:
            commission_amount = 0.0
            commission_total = 0.0
            
            commissions = commission_line_obj._get_sale_commission(cr, uid, 
                                   line.name, 
                                   order.user_id, 
                                   order.partner_id, 
                                   product, 
                                   line.product_uos_qty, 
                                   line.price_subtotal, 
                                   date=order.date_order, 
                                   pricelist=order.pricelist_id, 
                                   commission_custom = line.commission_custom,
                                   context=context)
            
            for c in commissions:
              commission_amount += c["amount"]
              commission += c["total_commission"]
            
          
        res[line.id] = {
          "commission": commission,
          "commission_amount": commission_amount,
          "commission_total": commission_total
        }
        
      return res
    
    
    _columns = {
      "commission": fields.function(_commission_fields, type="float", string="Commission %", multi="_commission_fields", readonly=True),
      "commission_custom": fields.float("Custom Commission %", readonly=True, states={"draft": [("readonly", False)], "sent": [("readonly", False)]}),
      "commission_amount": fields.function(_commission_fields, type="float", string="Commission Amount", multi="_commission_fields", readonly=True),
      "commission_total": fields.function(_commission_fields, type="float", string="Commission Amount", multi="_commission_fields", readonly=True)      
    }
    
    
    def _product_margin_extra(self, cr, uid, line, context=None):
      res = super(sale_order_line, self)._product_margin_extra(cr, uid, line, context=context)
      res += line.commission_amount        
      return res
    

    
