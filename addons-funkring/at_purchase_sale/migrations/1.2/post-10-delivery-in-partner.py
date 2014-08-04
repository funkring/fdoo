__name__ = "Correct address_id from pickings created from purchase order with destination address_id"

def migrate(cr,v):
    
    cr.execute("SELECT p.id, po.partner_id, po.partner_address_id FROM stock_picking p "
               " INNER JOIN purchase_order po ON po.id = p.purchase_id AND po.dest_address_id IS NOT NULL "
               " WHERE p.partner_id != po.partner_id " 
               " AND p.type='in' ")


    for row in cr.fetchall():
        picking_id = row[0]
        partner_id = row[1]
        address_id = row[2]
        cr.execute("UPDATE stock_picking SET partner_id=%s, address_id=%s WHERE id=%s",
                   (partner_id,address_id,picking_id) )
