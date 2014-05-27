# -*- coding: utf-8 -*-
__name__ = "Correct Mail Function Fields"

def migrate(cr,v):
    
    cr.execute("SELECT a.id, a.alias, d.complete_name FROM posix_mailalias AS a "
                   " INNER JOIN posix_domain d ON d.id = a.domain_id ")
    for row in cr.fetchall():         
        alias_id = row[0] 
        user_alias = row[1]
        user_domain = row[2]
        email = None
        
        if user_alias and user_domain:
            email=("%s@%s" % (user_alias,user_domain))
        cr.execute("UPDATE posix_mailalias SET email=%s WHERE id=%s",(email,alias_id))
    
      
