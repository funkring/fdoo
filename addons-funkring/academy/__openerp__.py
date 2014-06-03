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
    "name" : "oerp.at Academy",
    "description":"""
oerp.at Academy
===============

  * A module to easy handle courses/lessons for schools or other training institutes

    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "category" : "Academy",
    "depends" : ["at_base", "at_product", "at_resource"],
    "data" : ["security.xml",
              "menu.xml",
              "view/academy_trainer_view.xml",
              "view/academy_course_view.xml",
              "view/academy_topic_view.xml",
              "view/academy_contract_view.xml",
              "view/academy_journal_view.xml",
              "view/academy_location_view.xml"
              ],
    "auto_install" : False,
    "installable": True
}