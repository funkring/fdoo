# -*- coding: utf-8 -*-

import re
__name__ = "Sets first- and surname"

def migrate(cr,v):
    # get all partners where surname and firstname is not set
    cr.execute("""
               SELECT id, name, surname, firstname FROM res_partner where surname is Null and firstname is Null
               """)
    for partner_id in cr.fetchall():
        id = partner_id[0]
        name = partner_id[1]

        split = re.split("[ ]+", name)
        firstname = " ".join(split[-1:])
        surname   = " ".join(split[:-1])

        cr.execute("UPDATE res_partner SET surname = %s, firstname = %s WHERE id = %s", (surname, firstname, id))
