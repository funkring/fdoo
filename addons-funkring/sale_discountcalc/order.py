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

from openerp.osv import fields, osv
from openerp.addons.at_base import util
from openerp.addons.at_base import format
import openerp.addons.decimal_precision as dp
import re


class sale_order(osv.Model):
    
    def _amount_discount(self, cr, uid, ids, field_names, arg, context=None):
      res = {}
      tax_obj = self.pool["account.tax"]
      for obj in self.browse(cr, uid, ids, context):
        amount_wo_discount_taxed = 0.0
        amount_wo_discount_untaxed = 0.0
        
        for line in obj.order_line:
          taxes = tax_obj.compute_all(cr, uid, line.tax_id, line.price_unit, line.product_uom_qty,
                                         line.product_id.id, line.order_id.partner_id.id)
          
          amount_wo_discount_taxed += taxes['total_included']
          amount_wo_discount_untaxed += taxes['total']
        
        res[obj.id] = {
          "amount_wo_discount_taxed": amount_wo_discount_taxed,
          "amount_wo_discount_untaxed": amount_wo_discount_untaxed,
          "amount_discount_taxed": amount_wo_discount_taxed - obj.amount_total,
          "amount_discount_untaxed": amount_wo_discount_untaxed - obj.amount_untaxed 
        }
      return res
    
    _inherit = "sale.order"
    _columns = {
      "amount_wo_discount_taxed": fields.function(_amount_discount, string="Subtotal w/o Discount", digits_compute=dp.get_precision("Sale Price"), multi="_amount_discount"),
      "amount_wo_discount_untaxed": fields.function(_amount_discount, string="Subtotal w/o Discount (untaxed)", digits_compute=dp.get_precision("Sale Price"), multi="_amount_discount"),
      "amount_discount_taxed": fields.function(_amount_discount, string="Amount Discount", digits_compute=dp.get_precision("Sale Price"), multi="_amount_discount"),
      "amount_discount_untaxed": fields.function(_amount_discount, string="Amount Discount (untaxed)", digits_compute=dp.get_precision("Sale Price"), multi="_amount_discount")
    }


class sale_order_line(osv.Model):
  
  _re_discount = re.compile("^\\s*([0-9]+)[.,]{0,1}([0-9]*)\\s*%{0,1}$")
  _re_discount_price = re.compile("^=\\s*([0-9]+)[.,]{0,1}([0-9]*)\\s*$")
    
  def _parse_number(self, pattern, val):
    if not val:
      return None
    m = pattern.match(val)
    if m:
      return float(m.group(1)) + (float("0.%s" % (m.group(2) or 0)))
    return None
  
  def _discount_calc_get(self, cr, uid, ids, field_name, arg, context=None):
    res = dict.fromkeys(ids)
    
    f_price = format.LangFormat(cr, uid, context=context, obj=self, f="discount_price")
    f_discount = format.LangFormat(cr, uid, context=context, obj=self, f="discount")
    
    for obj in self.browse(cr, uid, ids, context):
      if obj.discount_price:
        res[obj.id] =  "=%s" % f_price.formatLang(obj.discount_price)
      elif obj.discount:
        res[obj.id] = "%s%%" % f_discount.formatLang(obj.discount)
    return res
  
  def _discount_calc_set(self, cr, uid, id, field_name, field_value, arg, context=None):
    discount_price = 0.0
    discount = 0.0
    
    if field_value:
      discount_price = self._parse_number(self._re_discount_price, field_value)
      if discount_price is None:
        discount = self._parse_number(self._re_discount, field_value)
      else:                
        values = self.read(cr, uid, id, ["price_unit", "product_uom_qty"], context=context)
        qty = values.get("product_uom_qty", 0.0)
        price_unit = values.get("price_unit", 0.0)
        total = qty * price_unit
        if total:
          discount = 100.0 - ((100.0 / (qty * price_unit)) * discount_price)
        
    self.write(cr, uid, id, {
      "discount_price": discount_price,
      "discount": discount      
    }, context=context)
    
  
  def write(self, cr, uid, ids, vals, context=None):
    res = super(sale_order_line, self).write(cr, uid, ids, vals, context=context)
    # update after change price
    if not "discount_calc" in vals and "price_unit" in vals or "product_uom_qty" in vals:
      for stored_vals in self.read(cr, uid, ids, ["discount_calc"], context=context):
        discount_calc = stored_vals.get("discount_calc")
        if discount_calc:
          self._discount_calc_set(cr, uid, val["id"], "discount_calc", discount_calc, None, context=context)
      
      
    return res
  
    
  _inherit = "sale.order.line"
  _columns = {
    "discount_price": fields.float("Price with Discount", required=True, digits_compute=dp.get_precision("Product Price"), readonly=True, states={"draft": [("readonly", False)]}),
    "discount_calc" : fields.function(_discount_calc_get, fnct_inv=_discount_calc_set, type="char", string="Discount", readonly=True, states={"draft": [("readonly", False)]}  )     
  }
