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
    "name" : "oerp.at Time Registration",
    "description":"""
HR Time Registration extensions
===============================
* Contract/Holiday based target hours
* Auto break
""",
    "version" : "1.0",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Human Resources",
    "depends" : ["at_hr","hr_contract","hr_holidays","hr_attendance"],
    "data" : ["security.xml",
              "view/daily_timesheet_view.xml",
              "view/event_type_view.xml",
              "view/timesheet_view.xml",                            
              "view/contract_view.xml",
              "report/employee_report.xml",
              "report/timesheet_report.xml"],
    "auto_install": False,
    "installable": True
}
