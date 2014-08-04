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

class product_eval_view(osv.osv):
    _name = "at_pos.product_eval_view"
    _description = "POS Product Evaluation View"
    _auto = False
    _columns = {
          "date": fields.date("Create Date", readonly=True),
          "year": fields.char("Year", size=4,readonly=True), 
          "month":fields.selection([("01","January"), ("02","February"), ("03","March"), ("04","April"),
            ("05","May"), ("06","June"), ("07","July"), ("08","August"), ("09","September"),
            ("10","October"), ("11","November"), ("12","December")], "Month",readonly=True),
          "day": fields.char("Day",size=10, readonly=True),
          "categ1_id" : fields.many2one("product.category","Category 1",readonly=True),
          "categ2_id" : fields.many2one("product.category","Category 2",readonly=True),
          "categ3_id" : fields.many2one("product.category","Category 3",readonly=True),          
          "leaf_categ_id" : fields.many2one("product.category","Leaf Category",readonly=True),
          "product_id" : fields.many2one("product.product","Product",readonly=True),
          "qty" : fields.float("Quantity"),
          "subtotal" : fields.float("Subtotal"),
          "lines" : fields.float("Lines")
    }    
    
    def init(self,cr):
        cr.execute("""
        CREATE OR REPLACE VIEW at_pos_product_eval_view AS ( 
        SELECT  
           MIN(l.id) as id,
           TO_DATE(TO_CHAR(l.create_date, 'dd-MM-YYYY'),'dd-MM-YYYY') AS date,
           TO_CHAR(l.create_date, 'YYYY') as year,
           TO_CHAR(l.create_date, 'MM') as month,
           TO_CHAR(l.create_date, 'YYYY-MM-DD') as day,
           rc.categ1_id AS categ1_id,
           rc.categ2_id AS categ2_id,
           rc.categ3_id AS categ3_id,
           rc.leaf_categ_id AS leaf_categ_id,
           p.id AS product_id,
           SUM(l.qty) AS qty,
           SUM(l.price_subtotal_incl) AS subtotal,
           COUNT(l.id) AS lines
           FROM pos_order_line AS l
             INNER JOIN pos_order AS o on o.id = l.order_id
             INNER JOIN product_product AS p ON p.id = l.product_id
             INNER JOIN product_template AS t ON t.id = p.product_tmpl_id
             INNER JOIN at_product_category_view AS rc ON rc.leaf_categ_id = t.categ_id
          GROUP BY 
              TO_DATE(TO_CHAR(l.create_date, 'dd-MM-YYYY'),'dd-MM-YYYY'),
              TO_CHAR(l.create_date, 'YYYY'),
              TO_CHAR(l.create_date, 'MM'),
              TO_CHAR(l.create_date, 'YYYY-MM-DD'),
              rc.categ1_id,
              rc.categ2_id,
              rc.categ3_id,
              rc.leaf_categ_id,
              p.id
        ) """)
   
product_eval_view() 