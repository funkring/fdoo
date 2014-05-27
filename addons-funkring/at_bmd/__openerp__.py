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
    "name" : "oerp.at BMD Export",
    "description":"""
oerp.at BMD Export
==================
* BMD Export
""",
    "version" : "1.0",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Accounting & Finance/Export",
    "depends" : ["mail","at_account","at_base"],    
    "data" : ["security.xml",       
              "wizard/bmd_export_wizard.xml",             
              "view/bmd_export.xml",
              "view/bmd_profil.xml",              
              "menu.xml"                    
             ],
    "auto_install": False,
    "installable": True
}
