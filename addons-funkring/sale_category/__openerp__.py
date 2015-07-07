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
    "name" : "oerp.at Sale category",
    "description":"""
oerp.at Sale category
=====================
  * Possibility to choose from different report layouts, with a single print button
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "category" : "Report",
    "depends" : ["at_account", "at_sale", "report_aeroo"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["view/sale_category_view.xml",
                    "view/account_invoice_view.xml",
                    "view/sale_order_view.xml",
                    "view/sale_shop_view.xml",
                    "menu.xml",
                    "security.xml"],
    "active": False,
    "installable": True
}
