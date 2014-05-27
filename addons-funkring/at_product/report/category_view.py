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

class category_view(osv.osv):
    _name="at_product.category_view"
    _description = "Category Second Normal Form View"
    _auto = False
    _columns = {                
        "categ1_id" : fields.many2one("product.category",'Category 1'),
        "categ2_id" : fields.many2one("product.category",'Category 2'),
        "categ3_id" : fields.many2one("product.category",'Category 3'),
        "leaf_categ_id" : fields.many2one("product.category",'Leaf Category')
    }
    
    def init(self,cr):
        cr.execute(""" 
            CREATE OR REPLACE VIEW at_product_category_view AS ( 
            SELECT 
              CASE WHEN c3.id IS NOT NULL THEN c3.id
                   WHEN c2.id IS NOT NULL THEN c2.id
                   ELSE c1.id
              END AS id,
              c1.id AS categ1_id,
              c2.id AS categ2_id,
              c3.id AS categ3_id,
              CASE WHEN c3.id IS NOT NULL THEN c3.id
                   WHEN c2.id IS NOT NULL THEN c2.id
                   ELSE c1.id
              END AS leaf_categ_id
              FROM product_category AS c1  
              LEFT JOIN product_category AS c2 ON c2.parent_id = c1.id
              LEFT JOIN product_category AS c3 ON c3.parent_id = c2.id
              WHERE c1.parent_id IS NULL 
             )        
        """)
category_view()