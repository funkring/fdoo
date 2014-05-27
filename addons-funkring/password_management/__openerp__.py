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
    "name" : "oerp.at Password Management",
    "description":"""
oerp.at Password Management
=========================================

 * Basic module to handle passwords for Openerp or external sites
 * Is able to save passwords from other partners

""",
    "version" : "1.1",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Generic Modules/Management",
    "depends" : ["at_base"],
    "data" : ["view/partner_view.xml",
                    "view/password_view.xml",
                    "security.xml"],
    "auto_install": False,
    "installable": True
}


