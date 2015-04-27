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
    "name" : "oerp.at E-Agency",
    "description":"""
oerp.at Employment Agency
=========================
* Module for employment agencies
* Client handling with special criteria, requirements and conditions
""",
    "version" : "1.0",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Agency",
    "depends" : ["base","at_base","mail"],
    "data" : ["security.xml",
              "menu.xml",
              "view/eagency_client_view.xml",
              "view/eagency_education_view.xml",
              "view/eagency_area_view.xml",
              "view/eagency_prof_status_view.xml",
              "view/eagency_lang_view.xml",
              "view/eagency_skill_view.xml"],
    "auto_install": False,
    "installable": True
}
