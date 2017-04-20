#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martinr@funkring.net>
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

# class purchase_order(osv.Model):
#     _inherit = "purchase.order"
#     
#     def wkf_approve_order(self, cr, uid, ids, context=None):
#         product_template_obj = self.pool["product.template"]
#         for order in self.browse(cr, uid, ids):
#             for line in order.order_line:
#                 if line.product_id:
#                     template_id = line.product_id.product_tmpl_id.id
#                     product_template_obj.write(cr, uid, template_id, {"standard_price" : line.price_unit})
#  
#         return super(purchase_order,self).wkf_approve_order(cr, uid, ids, context=context)

class purchase_order_line(osv.Model):
    _inherit = "purchase.order.line"
    _order = "name, id"