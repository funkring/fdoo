# -*- coding: utf-8 -*-
__name__ = "Correct project status"

def migrate(cr,v):
    cr.execute("""
UPDATE project_project SET state='new' WHERE id IN (
    SELECT p.id FROM sale_order o 
    INNER JOIN account_analytic_account a ON a.order_id = o.id 
    INNER JOIN project_project p ON p.analytic_account_id = a.id 
    WHERE o.state IN ('draft','sent') AND p.state = 'open'
)""")