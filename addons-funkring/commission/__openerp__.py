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
    "name" : "oerp.at Commission",
    "description":"""
Commission Base Module
======================

Basic module for commission management

""",
    "version" : "1.2",
    "author" :  "oerp.at",
    "category" : "Commission",
    "depends" : ["at_base",
                 "at_account",
                 "at_sale",
                 "analytic",
                 "product",
                 "sale_margin",
                 "automation"],
    "data" : ["security.xml",
              "menu.xml",
              "view/commission_task_view.xml",
              "view/company_view.xml",
              "view/commission_view.xml",
              "view/commission_invoice_wizard.xml",
              "view/analytic_view.xml",
              "view/product_view.xml",
              "view/product_category_view.xml",
              "data/product_categories.xml",
              "data/product_uom.xml"],
    "auto_install" : False,
    "installable": True
}
