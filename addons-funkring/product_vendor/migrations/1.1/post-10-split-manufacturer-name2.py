# -*- coding: utf-8 -*-
__name__ = "Split product name -> name2, manufacturer"

def migrate(cr,v):
    cr.execute("SELECT t.id, t.name, t.manufacturer, lg.lang, lg.src, lg.value, lg.id FROM product_template t "
               " LEFT JOIN ir_translation lg ON lg.name = 'product.template,name' AND lg.res_id = t.id ")
     
    for tmpl_id, name, manufacturer, lang, src, value, lg_id in cr.fetchall():        
        if not manufacturer:
            continue
        
        cur_name = value or name
        cr.execute("UPDATE product_template SET name2=%s WHERE id=%s", (cur_name, tmpl_id))
        
        new_value = "%s %s" % (manufacturer, cur_name)
        if lg_id:
            if not manufacturer in value:
                cr.execute("UPDATE ir_translation SET value=%s WHERE id=%s",(new_value, lg_id))                
        elif not manufacturer in name:
            cr.execute("UPDATE product_template SET name=%s WHERE id=%s",(new_value, tmpl_id))
            
        
                    