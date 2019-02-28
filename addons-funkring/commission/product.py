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
import openerp.addons.decimal_precision as dp
   
class product_category(osv.osv):
  
    _inherit = "product.category"
    _columns = {
        "delivery_cost" : fields.float("Deliver Costs", type="float",  digits_compute=dp.get_precision("Product Price"))        
    }
   
   
class product_template(osv.osv):
    
    _inherit = "product.template"
    _columns = {      
        "delivery_cost" : fields.related("product_variant_ids", "delivery_cost", type="float", string="Delivery Costs",  digits_compute=dp.get_precision("Product Price"))        
    }
    
    
class product_product(osv.osv):
    
    def _delivery_cost_co(self, cr, uid, ids, field_name, arg, context=None):
      res = dict.fromkeys(ids, 0.0)
      for obj in self.browse(cr, uid, ids, context):
        res[obj.id] = obj.delivery_cost or obj.categ_id.delivery_cost or 0.0 
      return res
    
       
    _inherit = "product.product"
    _columns = {
        "delivery_cost" : fields.float("Delivery Costs",  digits_compute=dp.get_precision("Product Price")),
        "delivery_cost_co": fields.function(_delivery_cost_co, string="Delivery Costs (Combined)", type="float", digits_compute=dp.get_precision("Product Price"))
    }
    
      
