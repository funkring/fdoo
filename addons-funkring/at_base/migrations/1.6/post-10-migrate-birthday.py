# -*- coding: utf-8 -*-
__name__ = "Convert date to birthday"

def migrate(cr,v):
    cr.execute("UPDATE res_partner SET birthday=date")