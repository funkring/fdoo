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
    "name" : "BMD Export",
    "description":"""
BMD Export
==========

* Export for accounting software BMD

""",
    "version" : "1.0",
    "author" :  "oerp.at",
    "website": "http://www.oerp.at",
    "category" : "Accounting",
    "depends" : ["mail",
                 "util_time",
                 "util_report",
                 "automation",
                 "at_account"],
    "data" : ["security/security.xml",
              "views/bmd_config_menu.xml",
              "views/export_profile_view.xml",
              "views/reconcil_profile_view.xml",
              "views/reconcil_view.xml",
              "views/export_line_view.xml",
              "views/export_view.xml"              
             ],
    "demo": [
        "demo/bmd_export_demo.xml",
    ],
    "auto_install": False,
    "installable": True
}
