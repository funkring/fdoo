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

class stock_picking(osv.Model):
    _inherit = "stock.picking"
    _columns = {
        "carrier_label_name" : fields.char("Carrier Label Name", copy=False, readonly=True),
        "carrier_label_pdf" : fields.binary("Carrier Label", copy=False, readonly=True),
        "carrier_api" : fields.related("carrier_id", "api", type="char", string="Carrier API", readonly=True),
        "carrier_status" : fields.selection([("packed","Packed"),
                                             ("delivered","Delivered"),
                                             ("received","Received"),
                                             ("rejected","Rejected"),
                                             ("returned","Returned")], string="Carrier Status", copy=False, readonly=True)
                
    }
    
    def action_carrier_label(self, cr, uid, ids, context=None):
        return True
    
    def action_carrier_cancel(self, cr, uid, ids, context=None):
        return True