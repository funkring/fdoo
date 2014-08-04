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
    "name" : "project_area",
    "description":"""
       A module for providing customers access to their projects
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Project Management",
    "depends" : ["analytic","project","at_base","at_project", "at_project_issue", "project_long_term"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["security.xml",
                    "view/timesheet_line_view.xml",
                    "view/project_view.xml",
                    "view/project_board.xml",
                    "view/project_issue_customer_view.xml",                                        
                    "view/project_issue_menu_customer_view.xml",                    
                    "view/project_ticket_board.xml",
                    "menu.xml"                   
                    ],
    "active": False,
    "installable": True
}
