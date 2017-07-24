# -*- coding: utf-8 -*-

__name__ = "Sets reminder name"

def migrate(cr,v):
    cr.execute(""" 
        SELECT p.id, c.name FROM account_dunning_profile p 
        INNER JOIN res_company c ON c.id=p.company_id WHERE p.name IS NULL
    """)
    for profile_id, name,  in cr.fetchall():
        cr.execute("UPDATE account_dunning_profile SET name=%s WHERE id=%s", (name, profile_id))
