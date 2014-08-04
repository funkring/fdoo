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
    "name" : "at_account_chartsync",
    "description":"""
       This module synchronizes the account_account_template with the account_account object
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "category" : "Account",
    "depends" : ["at_account", "at_base"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["view/chartsync_wizard.xml",],
    "active": False,
    "installable": True
}
