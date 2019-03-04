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
from openerp import api, fields

class commission_line(osv.Model):
  _inherit = "commission.line"

  @api.cr_uid_context
  def _validate_sale_commission(self, cr, uid, values, obj=None, company=None, context=None):
    commission = super(commission_line, self)._validate_sale_commission(cr, uid, values, obj=obj, context=context)
    if company:
      rule = company.cdisc_rule
      if rule and not company.cdisc_date or company.cdisc_date >= values["date"]:
        if rule == "mhalf":
          commission = self._cdisc_rule_mhalf(cr, uid, values, obj=obj, company=company, context=context)
          #commission = getattr(self, rule)(cr, uid, values, obj=obj, context=context)
          
    return commission
  
  
  def _cdisc_rule_mhalf(self, cr, uid, commission, obj=None, company=None, context=None):
      if commission.get("val_based") or not obj or obj._model._name != "sale.order.line"  or not obj.discount or obj.discount_action:
        return commission 
      
      percent = commission.get("base_commission", 0.0)
      if percent:
        # deduct 100% discount
        if percent >= 100.0:
          commission["base_commission"] = -100.0
          commission["total_commission"] = -100.0
          commission["amount"] = commission["price_sub"]
        else:
          # deduct discount
          taxes = self.pool["account.tax"].compute_all(cr, uid, obj.tax_id, obj.price_unit, obj.product_uom_qty,
                                    obj.product_id.id, obj.order_id.partner_id.id)
      
          amount = obj.price_subtotal   
          discount_amount = taxes['total'] - amount
          if discount_amount > 0:
            percent = percent - (obj.discount / 2.0)
            if percent < 0:
              percent = 0.0
            factor = (percent / 100.0)*-1
            commission["base_commission"] = percent
            commission["total_commission"] = percent
            commission["amount"] = commission["price_sub"] * factor
  
      return commission