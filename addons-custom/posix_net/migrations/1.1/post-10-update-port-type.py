# -*- coding: utf-8 -*-
__name__ = "Convert Port Type"

def migrate(cr,v):
    cr.execute("SELECT pt.id, utp.wlan_key_len FROM posix_net_port_type pt "
               " INNER JOIN posix_net_unit_type_port utp ON utp.port_type_id = pt.id ")

    for type_id, key_len in cr.fetchall():
        cr.execute("UPDATE posix_net_port_type SET key_len = %s WHERE id=%s",(key_len,type_id))

