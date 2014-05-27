# -*- coding: utf-8 -*-
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
    "name" : "oerp.at Dataset",
    "description":"""
oerp.at Dataset Extension
=========================

* define data models based on ERP models
* dynamic documents, structures like couchdb
* data views based on existing models

""",
    "version" : "1.0",
    "author" :  "funkring.net",
    "category" : "Tools",
    "depends" : ["web","at_base"],
    "data" : ["security.xml",
              "view/dataset_view.xml",
              "view/dataset_data_view.xml",
              "view/dataset_spec_view.xml"],
    "auto_install" : False,
    "installable": True,
}