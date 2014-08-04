__name__ = "Find pos payment for statement line"

def migrate(cr,v):
    
    cr.execute(" SELECT bl.id, p.id FROM account_bank_statement_line bl " 
               " INNER JOIN pos_order o ON o.id = bl.pos_statement_id "
               " INNER JOIN pos_order_payment p ON p.order_id = o.id AND p.amount = bl.amount ")

    for row in cr.fetchall():
        statement_line_id = row[0]
        payment_id = row[1]        
        cr.execute("UPDATE pos_order_payment SET statement_line_id = %s WHERE id=%s",(statement_line_id,payment_id))
