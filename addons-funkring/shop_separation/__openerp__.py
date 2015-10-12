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
    "name" : "oerp.at Shop Separation",
    "description":"""
oerp.at Shop Separation for Project and Sale
============================================

* Shop specific product categories
* Different project templates per shop
* Access rules for access only allowed project, task, 
  tickets and sale orders

""",
    "version" : "1.0",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Sales",
    "depends" : ["at_sale","at_project_sale"],
    "data" : ["view/user_view.xml", 
              "view/sale_view.xml",
              "view/shop_view.xml",  
              "view/project_view.xml",
              "view/project_issue_view.xml",   
              "security.xml"],
    "auto_install": False,
    "installable": True
}
