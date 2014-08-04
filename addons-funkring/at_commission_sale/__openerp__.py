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
    "name" : "at_commission_sale",
    "description":"""
       A module for creating commissions
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "category" : "Sales/Commission/Sales",
    "depends" : ["at_commission","at_sale"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["data/analytic_journals.xml",
                    "data/products.xml",
                    "data/properties.xml",
                    "view/pricelist_item_view.xml",
                    "view/crm_section_view.xml",
                    "view/bonus_view.xml",
                    "security.xml"],
    "active": False,
    "installable": True
}
