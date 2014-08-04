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
    "name" : "oerp.at Account Dunning",
    "description":"""
oerp.at Account Dunning
=======================

  * This module allows to completly handle the reminders
  * Single/multiple reminder (re)print
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "category" : "Accounting",
    "depends" : ["at_account"],
    "data" : ["view/account_dunning_view.xml",
              "view/account_reminder_view.xml",
              "view/account_invoice_view.xml",
              "view/partner_view.xml",
              "report/account_reminder_report.xml",
              "wizard/dunning_wizard.xml",
              "menu.xml",
              "security.xml",],
    "auto_install" : False,
    "installable": True
}