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

from openerp import models, fields, api, _

class res_company(models.Model):
  _inherit = "res.company"
  
  cdisc_date = fields.Date("Commission Rule Active From", help="If date is empty rule is used every time, if not rule is used for invoices, orders greater or equal to the entered date")
   
  cdisc_rule = fields.Selection([("mhalf",
                                  "Minus half discount")],
                                  string="Commission Rule",
                                  help="""Reflect Discount in Provision

Generally the provision was generated from the net total. With following rules
the behavior could be changed. 
 
* Minus half discount: On discount the provision was deducted by half discount

""")
      
  