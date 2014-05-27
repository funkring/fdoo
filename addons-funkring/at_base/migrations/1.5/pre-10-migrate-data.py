# -*- coding: utf-8 -*-
__name__ = "Delete moved data"

def migrate(cr,v):
 
   # move data   
    moves = [
             ("stock","procurement","sequence_mrp_op_type"),
             ("stock","procurement","sequence_mrp_op")
            ]
     
    for move in moves:
        cr.execute("UPDATE ir_model_data SET module=%s WHERE module=%s AND name=%s",move)
    
            
    # delete wrong view
    cr.execute("""
    SELECT v.id, d.id from ir_ui_view v
    INNER JOIN ir_model_data d ON d.id = v.model_data_id
    WHERE v.model IN ('product.category','product.product') AND d.module='stock'
    """)
    
    for view_id, data_id in cr.fetchall():
        cr.execute("DELETE FROM ir_ui_view WHERE id=%s", (view_id,))
        cr.execute("DELETE FROM ir_model_data WHERE id=%s",(data_id,))
        
    # delete wrong view
    cr.execute("""
    SELECT v.id, d.id from ir_ui_view v
    INNER JOIN ir_model_data d ON d.id = v.model_data_id
    WHERE d.name IN ('product_template_form_view_procurement',
                     'product_form_view_procurement_button') 
    """)
    
    for view_id, data_id in cr.fetchall():
        cr.execute("DELETE FROM ir_ui_view WHERE id=%s", (view_id,))
        cr.execute("DELETE FROM ir_model_data WHERE id=%s",(data_id,))