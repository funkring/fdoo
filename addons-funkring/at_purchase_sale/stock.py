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

class stock_picking(osv.osv):
        
    def _sender_address(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for picking in self.browse(cr, uid, ids, context):
            shop = picking.shop_id
            partner = None
            if shop:
                if shop.sender_address_id:
                    partner = shop.sender_address_id
                if not partner and shop.neutral_delivery and picking.partner_id:
                    partner = picking.partner_id         
                if not partner and picking.location_id:
                    partner = picking.location_id.partner_id
                if not partner and shop.warehouse_id:
                    partner = shop.warehouse_id.partner_id
                if not partner and shop.company_id.partner_id:
                    partner = shop.company_id.partner_id
                #
                if partner:
                    res[picking.id]=partner.id
        return res
        
    _inherit = "stock.picking"
    _columns = {
        "sender_address_id" : fields.function(_sender_address, string="Sender Address", type="many2one", obj="res.partner", store=False)
    }    
