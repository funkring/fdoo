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

class mrp_bom(osv.Model):
  
  def _product_categ_id(self, cr, uid, ids, field_name, arg, context=None):
    res = dict.fromkeys(ids)
    for obj in self.browse(cr, uid, ids, context):
      res[obj.id] = obj.product_tmpl_id.categ_id.id    
    return res
  
  def _relids_product_template(self, cr, uid, ids, context=None):
    cr.execute("SELECT id FROM mrp_bom WHERE product_tmpl_id IN %s", (tuple(ids),))
    return [r[0] for r in cr.fetchall()]
  
  _inherit = "mrp.bom"
  _columns = {
    "product_categ_id" : fields.function(_product_categ_id, string="Product Category", type="many2one", obj="product.category", store={
      "product.template" : (_relids_product_template,["categ_id"], 10),
      "mrp.bom": (lambda self, cr, uid, ids, context=None: ids, ["product_tmpl_id"], 10)
    })
  }