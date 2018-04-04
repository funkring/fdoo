# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martin.reisenhofer@funkring.net>
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
    "name" : "oerp.at Project + Sale",
    "description":"""
oerp.at Project + Sale
======================

* Possibility to automatically create an project for each sale order
* Configure the auto creation process


    """,
    "version" : "1.2",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Sales Management/Project Management",
    "depends" : ["at_project",
                 "at_sale",
                 "sale",
                 "account",
                 "account_analytic_analysis",
                 "project_timesheet",
                 "sale_margin",                 
                 "at_hr",
                 "sale_service",
                 "hr_timesheet_invoice"],
    "data" : [ 
                "security.xml",
                "view/analytic_account_view.xml",
                "view/sale_shop_view.xml",
                "view/sale_order_view.xml",
                "wizard/correct_time_wizard.xml",
                "view/task_view.xml",
                "view/partner_view.xml",
                "view/product_view.xml",
                "view/project_view.xml",
                "report/sale_order_report.xml",
                "report/account_invoice_report.xml",
                "report/account_analytic_entries_report.xml",
                "data/properties.xml",
                "data/recurring_task_cron.xml"
                ],
    "auto_install": False,
    "installable": True
}
