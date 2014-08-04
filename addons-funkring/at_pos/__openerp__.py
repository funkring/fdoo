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
    "name" : "at_pos",
    "description":"""
       POS (Point of Sale) Extensions for the Funkring.net POS Touch&Cash
    """,
    "version" : "1.1",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Sales",
    "depends" : ["at_base","at_product","point_of_sale","posix","product_code"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["report/bon_report.xml",
                    "report/cashbox_report.xml",
                    "report/product_eval_view.xml",
                    "wizard/cashbox_report.xml",                
                    "view/pos_view.xml",
                    "view/product_view.xml",
                    "view/company_view.xml",
                    "security.xml",
                    "view/pos_printer_view.xml",
                    "view/pos_system_view.xml",
                    "view/cash_statement_view.xml",
                    "menu.xml"],
    "active": False,
    "installable": True
}
