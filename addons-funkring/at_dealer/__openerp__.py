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
    "name" : "at_dealer",
    "description":"""
       An Basic Package for an Austrian Dealer with...
        * Shipping
        * Purchase
        * Stock         
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "category" : "Template",
    "depends" : ["account_cancel",
                 "at_base",                 
                 "at_account",
                 "at_account_report",
                 "at_sale",
                 "at_sale_report",
                 "at_stock",
                 "at_purchase",
                 "at_purchase_sale",
                 "at_purchase_report",
                 "at_mail_wizard_invoice",
                 "at_mail_wizard_sale",
                 "at_mail_wizard_purchase"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [],
    "active": False,
    "installable": True
}
