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
    "name" : "oerp.at Sale Cancel",
    "description":"""
oerp.at Sale Extensions
=======================

* allow cancel sale order with invoices
* allow cancel sale order with deliveries
* allow cancel sale order with purchase orders

""",
    "version" : "1.0",
    "author" :  "oerp.at",
    "website": "http://oerp.at",
    "category" : "Sales",
    "depends" : ["at_sale"],
    "data" : ["wizard/order_cancel_wizard.xml"],
    "auto_install": False,
    "installable": True
}
