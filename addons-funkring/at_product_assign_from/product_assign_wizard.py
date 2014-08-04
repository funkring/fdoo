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

from openerp.osv import fields,osv

class product_assign_wizard(osv.osv_memory):    
    _name = "product.assign_wizard"
    _description="Product Assign Wizard"
    _columns = {
        "category_id" : fields.many2one("product.category","Category",required=True),
        "product_id" : fields.many2one("product.product","Template",required=True),
        "product_type": fields.selection([("product","Stockable Product"),("consu", "Consumable"),("service","Service")], "Product Type", required=True),
        "assign_suppliers" : fields.boolean("Assign Suppliers")
    }
    
    def assign_to_products(self, cr, uid, ids, context=None):
        category_obj = self.pool.get("product.category")
        product_obj = self.pool.get("product.product")        
        for o in self.browse(cr, uid, ids,context=context):            
            categ_ids = category_obj.search(cr,uid,[("parent_id","child_of",o.category_id.id)])
            categ_ids.append(o.category_id.id)
            product_ids = product_obj.search(cr,uid,[("categ_id","in",categ_ids),("id","!=",o.product_id.id),("type","=",o.product_type)])
            
            if product_ids:
                if o.assign_suppliers:            
                    cr.execute("DELETE FROM product_supplierinfo WHERE product_id IN %s AND NOT product_id = %s",(tuple(product_ids),o.product_id.id))                                         
                    for seller in o.product_id.seller_ids:
                        sellerVals = {
                            "name" : seller.name.id,   
                            "sequence" : seller.sequence,                 
                            "min_qty" : seller.min_qty,
                            "delay" : seller.delay                    
                        }                    
                        product_obj.write(cr,uid,product_ids,{"seller_ids" : [(0,0,sellerVals)]},context)
        return {"type" : "ir.actions.act_window_close"}
            
    
product_assign_wizard()