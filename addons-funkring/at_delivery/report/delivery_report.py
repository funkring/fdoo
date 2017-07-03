# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.addons.at_base import extreport

class Parser(extreport.basic_parser):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "prepare": self._prepare
        })
        
    def _prepare(self, o):
        carrier = {}

        for picking in o.picking_ids:
            if picking.carrier_id:
                carrier_values = carrier.get(picking.carrier_id.id)
                if carrier_values is None:
                    carrier_values = {
                        "name" : picking.carrier_id.name,
                        "carrier" : picking.carrier_id,
                        "pickings" : [],
                        "packages" : 0,
                        "weight" : 0.0                        
                    }
                    carrier[picking.carrier_id.id] = carrier_values

                carrier_values["pickings"].append(picking)                
                carrier_values["packages"] = carrier_values["packages"] + picking.number_of_packages
                carrier_values["weight"] = carrier_values["weight"] +  picking.carrier_weight
                
        carrier = sorted(carrier.values(), key=lambda v: v["name"])
        return carrier
                