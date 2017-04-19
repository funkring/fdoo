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

class delivery_carrier_dpd(osv.Model):
    _name = "delivery.carrier.dpd"
    _description = "DPD Profile"
    _columns = {
        "name" : fields.char("Name", required=True),
        "user" : fields.char("User", required=True),
        "password" : fields.char("Password", password=True, required=True),
        "client" : fields.char("Client", required=True),
        "customerId" : fields.char("CustomerID")
    }
    

class delivery_carrier(osv.Model):
    _inherit = "delivery.carrier"
    
    def _api_select(self, cr, uid, context=None):
        res = super(delivery_carrier, self)._api_select(cr, uid, context=context)
        res.append(("dpd","DPD"))
        return res
    
    _columns = {
        "api" : fields.selection(_api_select, string="API"),
        "dpd_profile_id" : fields.many2one("delivery.carrier.dpd","DPD Profile"),
        "dpd_product1" : fields.selection([("NP","DPD/B2C Normal"),
                                           ("KP","DPD/B2C Small"),
                                           ("RETURN","DPD Return"),
                                           ("AM1","Service Business Day 09 AM"),
                                           ("AM2","Service Business Day 12 AM"),
                                           ("AM1-6","Service Saturday 09 AM"),
                                           ("AM2-6","Service Saturday 12 AM")],
                                          string="Product 1")
    }