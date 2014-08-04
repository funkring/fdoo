# -*- coding: utf-8 -*-
__name__ = "Correct PDF Attachments"

def migrate(cr,v):
    cr.execute("SELECT a.id, a.datas_fname, a.name FROM ir_attachment a")
    for id, datas_fname, name in cr.fetchall():
        if ".pdf.pdf" in datas_fname or ".pdf.pdf" in name:
            datas_fname = datas_fname.replace(".pdf.pdf", ".pdf")
            name = name.replace(".pdf.pdf", ".pdf")
            cr.execute("UPDATE ir_attachment SET datas_fname = %s, name=%s WHERE id=%s",(datas_fname,name,id))
