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
    "name" : "Automation",
    "summary" : "Implementation of a background task queue",
    "description":"""
Automation
==========

* Task queue
* Execute background tasks with status
* Task workflow

    """,
    "version" : "1.0",
    "author" :  "oerp.at",
    "website" : "http://oerp.at",
    "category" : "Automation",
    "depends" : ["at_base"],
    "data" : ["security.xml",
              "data/cleanup_cron.xml",
              "views/task_log.xml",
              "views/stage_view.xml",
              "views/task_view.xml",
              "views/cron_view.xml"],
    "auto_install" : False,
    "installable": True
}