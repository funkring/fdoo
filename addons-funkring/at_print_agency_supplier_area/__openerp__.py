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
    "name" : "at_print_agency_supplier_area",
    "description":"""
       Combines Print Agency with Supplier Area and adds additional functions like:
        * search and sort for format
        * search and sort for grammatur
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Agency/Supplier",
    "depends" : ["at_print_agency","supplier_area"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["view/supplier_view.xml"],
    "active": False,
    "installable": True
}
