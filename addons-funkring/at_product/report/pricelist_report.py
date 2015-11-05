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


from openerp.addons.at_base import extreport

class Parser(extreport.basic_parser):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "pricelist_versions": self._pricelist_versions
        })
        
    def _pricelist_view(self, version):
        product_map = {}
        category_list = []
        products_by_qty_by_partner = []
        category_map = {}
        
        def add_product(product):
            if not product.id in product_map:
                product_vals = {
                    "product" : product,
                    "price" :  product.list_price
                }
                # set to product map
                product_map[product.id] = product_vals         
                products_by_qty_by_partner.append((product, 1, None))       
                # check if category exist
                category_vals = category_map.get(product.categ_id.id)
                if not category_vals:
                    category_vals = {
                        "name" : product.categ_id.name,
                        "products" : []
                    }
                    category_list.append(category_vals)
                    category_map[product.categ_id.id]=category_vals
                    
                category_vals["products"].append(product_vals)
            
        
        for item in version.items_id:
            product = item.product_id                   
            if product:
                add_product(product)      
                
        # determine price
        pricelist_obj = self.pool.get("product.pricelist")
        price_dict = pricelist_obj._price_get_multi(self.cr, self.uid, version, products_by_qty_by_partner, self.localcontext)
        for product_id, price in price_dict.items():
            product_vals = product_map.get(product_id)
            if product_vals and price:
                product_vals["price"]=price
                
        return {
            "name" : version.name,
            "categories" : category_list,
            "currency" : version.pricelist_id.currency_id
        }
        
    def _pricelist_versions(self, o):
        if o._name == "product.pricelist.version":
            return [self._pricelist_view(o)]
        if o._name == "product.pricelist":
            version = o.active_version_id
            if version:
                return [self._pricelist_view(version)] 
        return []
        
        
        