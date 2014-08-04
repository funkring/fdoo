# -*- coding: utf-8 -*-
__name__ = "Correct Calendar Notification"

def migrate(cr,v):
    # Not sure if this is good
    #cr.execute("DELETE FROM ir_cron WHERE function like '%do_run_scheduler%'")
    pass
