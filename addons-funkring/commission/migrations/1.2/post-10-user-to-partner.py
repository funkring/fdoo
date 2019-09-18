# -*- coding: utf-8 -*-
__name__ = "convert user to partner"

def migrate(cr,v):
    # get new category 
    cr.execute("""UPDATE commission_task SET partner_id = res_users.partner_id 
      FROM res_users
      WHERE res_users.id = commission_task.user_id
        AND commission_task.partner_id IS NULL 
    """)