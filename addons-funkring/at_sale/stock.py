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

from openerp.osv import fields,osv

class stock_picking(osv.osv):

    def _create_invoice_from_picking(self, cr, uid, picking, vals, context=None):
        if picking and picking.shop_id:
            vals["shop_id"] = picking.shop_id.id
        return super(stock_picking,self)._create_invoice_from_picking(cr, uid, picking, vals, context=context)

    _inherit = "stock.picking"
    _columns = {
        "shop_id" : fields.related("sale_id","shop_id",type="many2one",relation="sale.shop",string="Shop",readonly=True,store=False,select=True)
    }
