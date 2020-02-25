# -*- coding: utf-8 -*-
__name__ = "convert user to partner"

def migrate(cr,v):
  
    cr.execute("""SELECT column_name 
      FROM information_schema.columns 
      WHERE table_name='commission_task' and column_name='user_id'""")
    
    if cr.fetchall():
      cr.execute("""UPDATE commission_task SET partner_id = res_users.partner_id 
        FROM res_users
        WHERE res_users.id = commission_task.user_id
          AND commission_task.partner_id IS NULL 
      """)