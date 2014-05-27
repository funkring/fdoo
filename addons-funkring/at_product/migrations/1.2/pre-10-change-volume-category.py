# -*- coding: utf-8 -*-
__name__ = "Correct uom category"

def migrate(cr,v):
    # get new category 
    cr.execute("""
       SELECT res_id  FROM ir_model_data d
         WHERE d.name='product_uom_categ_vol' AND d.module='product'
    """)
    for category_id in cr.fetchall():
        # get m3
        cr.execute("""
           SELECT res_id  FROM ir_model_data d
             WHERE d.name='product_uom_m3' AND d.module='at_product'
        """)
        for res_id in cr.fetchall():
            cr.execute("UPDATE product_uom SET category_id = %s WHERE id = %s", (category_id, res_id))
