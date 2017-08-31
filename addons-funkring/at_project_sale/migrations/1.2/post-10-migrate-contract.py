# -*- coding: utf-8 -*-
__name__ = "Determine Contract"

def migrate(cr,v):
    cr.execute("UPDATE account_analytic_account SET is_contract=true WHERE order_id IS NULL AND (recurring_invoices OR invoice_on_timesheets OR fix_price_invoices)")