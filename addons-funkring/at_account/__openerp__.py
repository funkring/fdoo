#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martinr@funkring.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "oerp.at Accounting and Finance",
    "description":"""
oerp.at Accounting and Finance Extensions
=========================================

 * Basic utility functions for depend modules
 * Direct invoice link in bank statement
 * Pre defined invoice Text for all kind of invoices
 * Aeroo report replacement
 * Tax Crossover - Ust and Vst merged into one

""",
    "version" : "1.1",
    "author" :  "funkring.net",
    "category" : "Accounting & Finance",
    "website": "http://www.funkring.net",
    "depends" : ["account",
                 "account_voucher",
                 "at_base",
                 "at_product"],
    "data" :       ["report/account_invoice_report.xml",
                    "report/account_voucher_list_report.xml",
                    "report/account_invoice_list_report.xml",
                    "report/account_bank_statement_report.xml",
                    "report/account_account_report.xml",
                    "view/account_journal_view.xml",
                    "view/account_bank_statement_view.xml",
                    "view/company_view.xml",
                    "wizard/invoice_attachment_wizard.xml",
                    "view/invoice_view.xml",
                    "menu.xml",
                    "security.xml"],
    "installable": True,
    "application" : True
}
