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

from at_sale_report import sale_order_report

class Parser(sale_order_report.Parser):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "prepare" : self.prepare,
            "optional_sum" : self.optional_sum
        })
    
    def optional_sum(self, sale_order):
        line_ids = []
        order_line_obj = self.pool.get("sale.order.line")
        
        for line in sale_order.order_line:
            formation = line.formation_id
            if formation.print_optional:
                line_ids.append(line.id)
                
        return order_line_obj._line_sum(self.cr, self.uid, line_ids)
    
    def prepare(self, sale_order):
        res = super(Parser, self).prepare(sale_order)
        res_value = {}
        
        formation_obj = self.pool.get("sale.order.formation")        
        formation_root_ids = formation_obj.search(self.cr,self.uid,[("order_id","=",sale_order.id),("parent_id","=",None)])
        res_value["formations"] = formation_obj._formation_structs_get(self.cr,self.uid,formation_root_ids,context=self.localcontext)
        res.append(res_value)
        
        return res
