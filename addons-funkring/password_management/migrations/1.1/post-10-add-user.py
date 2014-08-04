__name__ = "Extract User from current Password Entries"

def migrate(cr,v):
    cr.execute("SELECT id, name, login FROM password_entry")
    for oid, name, login in cr.fetchall():
        if name:
            tokens = name.split(":")
            if not login and len(tokens) == 2:
                name = tokens[0].strip()
                login = tokens[1].strip()
                
            if name:
                cr.execute("UPDATE password_entry SET subject=%s WHERE id=%s", (name, oid))
            if login:
                cr.execute("UPDATE password_entry SET login=%s WHERE id=%s", (login, oid))
