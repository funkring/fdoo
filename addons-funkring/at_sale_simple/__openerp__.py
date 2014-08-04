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
    "name" : "at_sale_simple",
    "description":"""
       Simplifies the standard sale module
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Sales",
    "website" : "http://www.funkring.net",
    "depends" : ["sale_crm","at_base","at_sale"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ['groups.xml',
                    'view/partner_view.xml',
                    'view/opportunity_view.xml',
                    'view/phonecall_view.xml',
                    'view/meeting_view.xml',                   
                    'view/product_view.xml',
                    'wizard/customer_request_view.xml',
                    'sale_menu.xml'],
    "active": False,
    "installable": True
}
