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

class mrp_bom(osv.Model):
    
    def _cost(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            cost = obj.product_id.standard_price
            if not cost:
                lines = obj.bom_lines
                if lines:
                    for line in lines:
                        sub_cost = line.product_id.standard_price*line.product_qty                
                        if not sub_cost:
                            sub_cost=self.read(cr,uid,line.id,["cost"],context=context)["cost"]
                        cost+=sub_cost
            res[obj.id]=cost*obj.product_qty        
        return res
    
    _name = "mrp.bom"
    _inherit = "mrp.bom"
    _columns = {
        "cost" : fields.function(_cost,string="Cost")
    }