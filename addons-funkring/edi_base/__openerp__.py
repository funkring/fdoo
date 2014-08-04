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
    "name" : "edi_base",
    "description":"""
       Basic EDI (Electronic Data Interchange) Modul
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "category" : "EDI",
    "depends" : ["at_base","base_tools"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["security.xml",
                    "menu.xml",
                    "view/system_view.xml",
                    "view/client_profile_view.xml",
                    "view/server_profile_view.xml",
                    "view/edi_transfer_view.xml",
                    "data/properties.xml",
                    "data/schedule.xml"
                    ],
    "active": False,
    "installable": True
}
