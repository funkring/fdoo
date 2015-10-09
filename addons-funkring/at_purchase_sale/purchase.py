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

from openerp.osv import fields,osv

class purchase_order(osv.osv):
    
    _inherit = "purchase.order"
    _columns = {    
        "sale_order_id" : fields.many2one("sale.order","Sale Order", states={"confirmed":[("readonly",True)], "approved":[("readonly",True)],"done":[("readonly",True)]}, ondelete="set null", copy=False),
        "shop_id" : fields.related("sale_order_id","shop_id",type="many2one",relation="sale.shop",string="Shop",readonly=True,store=False,select=True)
    }


class purchase_order_line(osv.osv):
    
    _inherit = "purchase.order.line"
    _columns = {
       "sale_line_id" : fields.many2one("sale.order.line", "Sale Order Line", readonly=True, copy=False, ondelete="set null"),
    } 
