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
    "name" : "supplier_area",
    "description":"""
       Supplier Portal for seeing its purchase/procurement orders
    """,
    "version" : "version",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Sales",
    "depends" : ["at_sale",
                 "at_purchase",
                 "at_purchase_sale",
                 "at_purchase_sale_quote_request",
                 "at_project_issue",
                 "at_stock",
                 "at_stock_report"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["security.xml",
                    "security_tmpl.xml",
                    "wizard/delivery_today_wizard.xml",
                    "wizard/delivery_today_stock_wizard.xml",
                    "report/delivery_report.xml",
                    "report/delivery_stock_report.xml",
                    "view/supplier_view.xml",
                    "view/supplier_board.xml",
                    "view/purchase_board.xml",
                    "menu.xml",                    
                    "wizard/purchase_stage_wizard.xml"],
    "active": False,
    "installable": True
}
