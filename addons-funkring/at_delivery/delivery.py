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


class delivery_carrier(osv.Model):
    _inherit = "delivery.carrier"
    
    def _api_select(self, cr, uid, context=None):
        return []
    
    _columns = {
        "api" : fields.selection(_api_select, string="API")
    }


class delivery_order(osv.Model):
    _name = "delivery.order"
    _description = "Delivery Order"
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get("name", "/") == "/":
            vals['name'] = self.pool.get("ir.sequence").get(cr, uid, "delivery.order", context=context) or "/"
        res = super(delivery_order, self).create(cr, uid, vals, context=context)
        return res
    
    def action_collect_picking(self, cr, uid, ids, context=None):
        for order_id in ids:
            picking_obj = self.pool["stock.picking"]
            picking_ids = picking_obj.search(cr, uid, [("state","=","done"),("carrier_id","!=",False),("carrier_order_id","=",False),("carrier_status","!=",False)], context=context)
            picking_obj.write(cr, uid, picking_ids, {
                "carrier_order_id" : order_id
            }, context=context)
        return True
    
    _columns = {
        "name" : fields.char("Name", required=True),
        "date" : fields.date("Date", required=True),
        "user_id" : fields.many2one("res.users", "User", ondelete="restrict", required=True),
        "picking_ids": fields.one2many("stock.picking", "carrier_order_id", "Pickings")
    }
    
    _defaults = {
        "name": lambda obj, cr, uid, context: '/',
        "date" : fields.datetime.now,
        "user_id": lambda obj, cr, uid, context: uid
    }
    
