__name__ = "Fill dest_address_id address from sales order"

def migrate(cr,v):
    
    cr.execute(" SELECT l.order_id, l.id, o.partner_shipping_id FROM purchase_order_line l "
               " INNER JOIN sale_order o ON o.id = l.sale_order_id AND o.supplier_ships "
               " WHERE l.dest_address_id IS NULL ")


    for row in cr.fetchall():
        purchase_order_id = row[0]
        purchase_line_id = row[1]
        address_id = row[2]
        cr.execute("UPDATE purchase_order SET dest_address_id = %s WHERE id=%s",(address_id,purchase_order_id))
        cr.execute("UPDATE purchase_order_line SET dest_address_id = %s WHERE id=%s",(address_id,purchase_line_id))
