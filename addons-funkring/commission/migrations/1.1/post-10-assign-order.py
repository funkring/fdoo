# -*- coding: utf-8 -*-
__name__ = "assign order from order line"

def migrate(cr,v):
    # get new category 
    cr.execute("""UPDATE commission_line SET order_id = sale_order_line.order_id
      FROM sale_order_line
      WHERE sale_order_line.id = commission_line.order_line_id 
        AND commission_line.order_id IS NULL
    """)