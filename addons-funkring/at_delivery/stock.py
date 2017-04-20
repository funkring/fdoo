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
        "carrier_label" : fields.binary("Carrier Label", copy=False, readonly=True),
        "carrier_error" : fields.text("Carrier Error", copy=False, readonly=True),
        "carrier_api" : fields.related("carrier_id", "api", type="char", string="Carrier API", readonly=True),
        "carrier_status" : fields.selection([("created","Created"),
                                             ("delivered","Delivered"),
                                             ("received","Received"),
                                             ("rejected","Rejected"),
                                             ("returned","Returned")], string="Carrier Status", copy=False, readonly=True)
                
    }
    
    def action_print_label(self, cr, uid, ids, context=None):
        for picking in self.browse(cr, uid, ids, context=context):
            # check if carrier api
            if picking.carrier_api:
                # check if label should created
                if not picking.carrier_label or not picking.carrier_status:
                    self.action_carrier_label(cr, uid, [picking.id], context=context)
                # create link for download
                return {
                    "url" : "/picking/%s/label.pdf" % picking.id,
                    #"url" : "/web/binary/saveas?model=stock.picking&field=carrier_label&id=%s&filename_field=carrier_label_name" % picking.id,
                    "type" : "ir.actions.act_url"
                }
        return True
    
    def action_carrier_label(self, cr, uid, ids, context=None):
        return True
    
    def action_carrier_cancel(self, cr, uid, ids, context=None):
        return True