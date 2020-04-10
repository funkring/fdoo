# -*- coding: utf-8 -*-

__name__ = "delete not linked lines"

def migrate(cr, version):
    cr.execute("DELETE FROM bmd_export_line WHERE bmd_export_id IS NULL")
