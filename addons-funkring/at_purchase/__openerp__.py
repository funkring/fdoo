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
    "name" : "oerp.at Purchase",
    "description":"""
oerp.at Purchase Base
=====================

* Purchase line priority
* Purchase line severity
* Additional functions, function fields, helpers around pickings
* Supplier unit price
* Supplier invoiced flag
* Directory name (for webdav,ftp)
* Mail Support for Purchase Order
* Aeroo Reports
""",
    "version" : "1.0",
    "author" :  "funkring.net",
    "category" : "Purchase",
    "website": "http://www.funkring.net",
    "depends" : ["at_procurement","purchase","procurement_jit"],
    "data" : ["security.xml",
              "menu.xml",
              "view/purchase_line_level.xml",
              "report/purchase_order_report.xml",
              "report/purchase_quote_request_report.xml"],
    "auto_install": False,
    "installable": True
}
