# -*- coding: utf-8 -*-
__name__ = "Convert Port Modes"

def migrate(cr,v):
    cr.execute("SELECT p.id, m.type FROM posix_net_port p "
               " INNER JOIN posix_net_port_mode m on m.id = p.mode_id ")
    
    for port_id, mode in cr.fetchall():
        cr.execute("UPDATE posix_net_port SET mode = %s WHERE id=%s",(mode,port_id))
