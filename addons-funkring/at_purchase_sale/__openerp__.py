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
    "name" : "oerp.at Purchase + Sale",
    "description":"""
oerp.at Purchase + Sale combination
===================================
* extension of stock_sale
* supplier shipment
* preferred supplier in order line
* delivery report
* neutral delivery
""",
    "version" : "1.2",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Sale Management/Purchase Management",
    "depends" : ["sale",
                 "sale_stock",
                 "delivery",
                 "at_stock",
                 "at_purchase",
                 "at_sale",
                 "at_product"],
    "data" : ["security.xml",
              "view/shop_view.xml",
              "view/sale_order_view.xml",
              "view/purchase_view.xml",
              "view/picking_view.xml",
              "view/stock_widget.xml",
              "report/stock_picking_report.xml",
              "report/stock_delivery_label.xml",
              "report/purchase_delivery_report.xml"],
    "qweb": ["static/src/xml/picking.xml"],
    "auto_install": False,
    "installable": True
}
