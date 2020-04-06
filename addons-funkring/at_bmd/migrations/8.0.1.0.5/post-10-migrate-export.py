# -*- coding: utf-8 -*-

import re

from openerp import api, SUPERUSER_ID


__name__ = "migrate BMD export"

def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        bmd_export_obj = env["bmd.export"]
        task_obj = env["automation.task"]
        
        cr.execute("SELECT id, name FROM bmd_export WHERE task_id IS NULL")
        for bmd_export_id, name in cr.fetchall():
            task = task_obj.create({
                "name": name,
                "res_model": "bmd.export",
                "res_id": bmd_export_id                
            })
            bmd_export_obj.browse(bmd_export_id).write({
                "task_id": task.id
            })
        
