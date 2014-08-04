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
    "name" : "oerp.at Base Modul",
    "description":"""
oerp.at Framework Basics
========================

Basic Module with a Set of Utils for further Funkring
Modules

* Aeroo report support
* Utils
* Basic wizards 

""",
    "version" : "1.5",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Base",
    "depends" : ["base",
                 "base_city",
                 "report",
                 "report_aeroo",
                 "report_aeroo_ooo",
                 "report_aeroo_printscreen"],    
    "data" : ["sequence_tmpl.xml",
              "view/partner_view.xml",
              "wizard/info_wizard.xml",
              "view/log_view.xml",
              "wizard/log_wizard.xml",
              "security.xml"],
    "auto_install" : False,
    "installable": True
}
