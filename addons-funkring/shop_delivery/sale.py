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

from openerp.osv import fields, osv

class sale_shop(osv.Model):
    _inherit = "sale.shop"
    _columns = {
        "carrier_id" : fields.many2one("delivery.carrier", "Carrier")
    }
    

class sale_order(osv.Model):
    _inherit = "sale.order"
    
    def onchange_shop_id(self, cr, uid, ids, shop_id, state, project_id, context=None):
        res = super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id, state, project_id, context=context)
        if shop_id:
            shop = self.pool["sale.shop"].browse(cr, uid, shop_id, context=context)
            if shop.carrier_id:
                res["value"]["carrier_id"] = shop.carrier_id.id
        return res
