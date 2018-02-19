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

class SaleLayoutCategory(osv.Model):
    _inherit = "sale_layout.category"
    _columns = {
        "order_id" : fields.many2one("sale.order", "Order", ondelete="cascade")
    }


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
