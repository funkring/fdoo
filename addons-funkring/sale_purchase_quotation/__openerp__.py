# -*- encoding: utf-8 -*-
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
    "name": "oerp.at Sale Purchase Quotation",
    "version": "1.0",
    "author": "Funkring",
    "website": "http://www.funkring.net",
    "category": "Sales",
    "sequence": 1,
    "complexity": "easy",
    "description": """
oerp.at Sale Purchase Quotation
===============================

* Adds possibility to do a purchase request within sale order lines of draft sale orders.
* Adds table to of available suppliers of selected product.
* Adds possibility to send email to any single or all suppliers.
* Allows to set cost price for each available product supplier.
* Adds possibility to select any supplier for each sale order line.""",
    "depends": ["at_sale",
                "at_purchase_sale",
                "at_stock",
                "at_mail",
                "mail",
                "sale_margin"],
    "data": ["view/sale_view.xml",
             "data/email_template.xml",
             "view/quotation_widget.xml",
             "view/sale_order_report_view.xml"],
    "installable": True,
    "auto_install": False,
    "application": True,
    "qweb" : ["static/src/xml/quotation.xml"]
}
