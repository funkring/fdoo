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
from pygments.lexer import _inherit

class SaleLayoutCategory(osv.Model):
    _inherit = "sale_layout.category"
    _columns = {
        "order_id" : fields.many2one("sale.order", "Order", ondelete="cascade")
        #"group_by_prod_categ" : fields.boolean("Order by Product Category")
    }
    

# def grouplines(self, ordered_lines, sortkey):
#     """Return lines from a specified invoice or sale order grouped by category"""
#     grouped_lines = []
#     for key, valuesiter in groupby(ordered_lines, sortkey):
#         group = {}
#         group['category'] = key
#         group['lines'] = list(v for v in valuesiter)
# 
#         if key.subtotal:
#             group['subtotal'] = sum(line.price_subtotal for line in group['lines'])
#         if key.group_by_prod_categ:
#             group['prod_categ'] = groupby(group['lines'], lambda x: x.product_id.categ_id if x.product_id else '')
#         grouped_lines.append(group)
#     return grouped_lines


class sale_order(osv.Model):
    _inherit = "sale.order"
    _columns = {
        "layout_categ_ids" : fields.one2many("sale_layout.category", "order_id", "Layout Categories")
    }
    

class sale_order_line(osv.Model):
    _inherit = "sale.order.line"
    _columns = {
        "prod_categ_id" : fields.related("product_id", "categ_id", string="Category", type="many2one", relation="product.category", readonly=True)
     } 