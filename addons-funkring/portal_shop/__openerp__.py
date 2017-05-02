# -*- coding: utf-8 -*-
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
    "name" : "oerp.at Shop Portal",
    "summary" : "Sales for non employee salesman",
    "description":"""
Shop for external salesman
==========================
* Extended portal security to create sale orders
    """,
    "version" : "1.0",
    "author" :  "oerp.at",
    "website" : "http://oerp.at",
    "category" : "Sales",
    "depends" : ["portal",
                 "sale",
                 "account_analytic_analysis",
                 "at_sale",
                 "at_purchase_sale",       
                 "shop_separation",
                 "sale_stock",
                 "portal_sale_base",
                 "portal_project",
                 "delivery"],
    "data" : ["security.xml",
              "menu.xml",
              "view/sale_view.xml",
              "view/portal_project_view.xml",
              "view/partner_view.xml"],
    "auto_install" : False,
    "installable": True
}