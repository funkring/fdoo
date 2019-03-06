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
from babel.numbers import NUMBER_PATTERN

NUMBER_PATTERN = "([" + re.escape("+-") + "]{0,1})([0-9]+)[.,]{0,1}([0-9]*)"

def parse_number(pattern, val):
  if not val:
    return None
  m = pattern.match(val)
  if m:
    sign = 1.0
    if m.group(1) == "-":
      sign = -1.0
    return (float(m.group(2)) + (float("0.%s" % (m.group(3) or 0))))*sign
  return None


class sale_order_line(osv.Model):
  
  _re_discount = re.compile("^\\s*" + NUMBER_PATTERN +"\\s*%{0,1}$")
  _re_discount_price = re.compile("^[" + re.escape("=-*") + "]\\s*"+ NUMBER_PATTERN + "\\s*$")
  
  def _parse_number(self, pattern, val):
    if not val:
      return None
    m = pattern.match(val)
    if m:
      sign = 1.0
      if m.group(1) == "-":
        sign = -1.0
      return (float(m.group(2)) + (float("0.%s" % (m.group(3) or 0))))*sign
    return None
  
  def _discount_calc_get(self, cr, uid, ids, field_name, arg, context=None):
    res = dict.fromkeys(ids)
    
    f_price = format.LangFormat(cr, uid, context=context, obj=self, f="discount_price")
    f_discount = format.LangFormat(cr, uid, context=context, obj=self, f="discount")
    
    for obj in self.browse(cr, uid, ids, context):
      val = []
      if obj.discount_action:
        val.append("!")
      if obj.discount_price:
        if obj.discount_unit:
          val.append("*%s" % f_price.formatLang(obj.discount_price))
        else:
          val.append("=%s" % f_price.formatLang(obj.discount_price))
      elif obj.discount:
        val.append("%s%%" % f_discount.formatLang(obj.discount))
      res[obj.id] = "".join(val) or None
      
    return res
  
  def _discount_calc_set(self, cr, uid, id, field_name, field_value, arg, context=None):
    discount_price = 0.0
    discount = 0.0
    discount_action = False
    discount_unit = False
    
    if field_value:
      if field_value[0] == "!":
        field_value = field_value[1:]
        discount_action = True
      
      discount_price = parse_number(self._re_discount_price, field_value)
      if not discount_price is None:                
        values = self.read(cr, uid, id, ["price_unit", "product_uom_qty"], context=context)
        qty = values.get("product_uom_qty", 0.0)
        price_unit = values.get("price_unit", 0.0)
        total = qty * price_unit
        if field_value[0] == "-":
          discount_price = total - discount_price
        if total:      
          if field_value[0] == "*":
            discount_unit = True   
            
            if discount_price < 0:
              discount_price = price_unit + discount_price     
            
            discount_unit_price = discount_price
            discount = 100.0 - ((100.0 / (qty * price_unit)) * (qty * discount_unit_price))
          else:    
            discount = 100.0 - ((100.0 / (qty * price_unit)) * discount_price)
      else:
        discount = parse_number(self._re_discount, field_value)
        
    self.write(cr, uid, id, {
      "discount_price": discount_price,
      "discount": discount,
      "discount_action": discount_action,
      "discount_unit": discount_unit
    }, context=context)
    
  
  def write(self, cr, uid, ids, vals, context=None):
    res = super(sale_order_line, self).write(cr, uid, ids, vals, context=context)
    # update after change price
    if not "discount_calc" in vals and "price_unit" in vals or "product_uom_qty" in vals:
      for stored_vals in self.read(cr, uid, ids, ["discount_calc"], context=context):
        discount_calc = stored_vals.get("discount_calc")
        if discount_calc:
          self._discount_calc_set(cr, uid, stored_vals["id"], "discount_calc", discount_calc, None, context=context)
    return res
  
    
  _inherit = "sale.order.line"
  _columns = {
    "discount_unit": fields.boolean("Unit Discount", readonly=True, states={"draft": [("readonly", False)]}),
    "discount_action": fields.boolean("Action", states={"draft": [("readonly", False)]}),
    "discount_price": fields.float("Price with Discount", digits_compute=dp.get_precision("Product Price"), readonly=True, states={"draft": [("readonly", False)]}),
    "discount_calc" : fields.function(_discount_calc_get, fnct_inv=_discount_calc_set, type="char", string="Discount", readonly=True, states={"draft": [("readonly", False)]},
                                      help="""Rabatt Functions

! action, could be always prefixed
= total price
* unit price
- rabatt
*- unit rabatt

if no sign is prefixed or % is used at the end, then it is percentage value
                                    
""")     
  }
