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

class product_product(osv.osv):
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(product_product,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type=="search":
            shop_id = context.get("shop",None)                        
            if shop_id:
                fields=res.get('fields',None)
                if fields:
                    field_categ_id =  fields.get('categ_id',None)
                    if field_categ_id:
                        shop_obj = self.pool.get("sale.shop")
                        category_obj  = self.pool.get("product.category")
                        category_ids = shop_obj.get_category_ids(cr,uid,shop_id)
                        if category_ids:         
                            categories = category_obj.browse(cr,uid,category_ids,context)
                            category_select = []
                            for category in categories:
                                category_select.append((category.id,category.name))                                                                
                            field_categ_id["selection"] = category_select
                
        return res
    
    _inherit = "product.product"
