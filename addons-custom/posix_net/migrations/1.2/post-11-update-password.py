# -*- coding: utf-8 -*-
import openerp

__name__ = "Convert Password"

def migrate(cr,v):
    pool = openerp.registry(cr.dbname)
    password_obj = pool.get("password.entry")
    cr.execute("SELECT id, name, \"user\", password, provider_id, description, group_id FROM posix_net_unit WHERE password_id IS NULL")    
    for oid, name, user, password, provider_id, description, group_id in cr.fetchall():
        password_id = password_obj.create(cr,1,{ 
            "subject" : name,
            "login" : user,
            "password" : password,
            "partner_id" : provider_id,
            "group_id" : group_id,
            "description" : description
        })
        cr.execute("UPDATE posix_net_unit SET password_id = %s WHERE id=%s",(password_id,oid))
