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
from at_base import util
    
class sale_order_formation(osv.osv):
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id'] and (not context or context.get("show_parent",True)):
                name = record['parent_id'][1]+'.'+name
            res.append((record['id'], name))
        return res
    
    def _complete_pos(self, cr, uid, ids, field_name, args, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+'.'+name
            res.append((record['id'], name))
        return dict(res)

    def _relids_order_formation(self, cr, uid, ids, context=None):
        res = []
        res.extend(self.search(cr, uid, [("parent_id", "child_of", ids)]))
        return res
    
    def _formation_struct_get(self,cr,uid,formation,include_childs=True,context=None):
        """ RETURN: {
            formation : browse<sale.order.formation>, 
            lines : [browse<sale.order.line,1>,browse<sale.order.line,2>],        # Sale Order Lines
            sum_print : { ... }      # total exclusive all non printing and optional for formations see sale.order.line->_line_sum
            sum_lines : { ... }      # total sum of lines
            childs : [{
                ...same, only if include_childs=True
            }]
        } """
        lines = []
        
        pos = 1
        for line in formation.line_ids:
            line_dict = {}
            line_dict["pos"] = pos
            line_dict["line"] = line
            lines.append(line_dict)
            pos+=1
        line_obj = self.pool.get("sale.order.line")
        
        line_ids = [x.id for x in formation.line_ids]
        sum_lines = line_obj._line_sum(cr,uid,line_ids,context=context)
        sum_print = sum_lines.copy()
        childs = []
        
        if include_childs:
            for child in formation.child_ids:
                if child.print_formation:
                    child_res = self._formation_struct_get(cr, uid, child, include_childs=include_childs, context=context)
                    util.sumUp(sum_print,child_res["sum_print"])                    
                    childs.append(child_res)                    
                    
        res = {         
            "formation" : formation,
            "lines" : lines,
            "sum_print" : sum_print,
            "sum_lines" : sum_lines,
            "childs" : childs,
        }
        return res
    
    def _formation_structs_get(self,cr,uid,ids,include_childs=True,context=None):
        res = []
        for formation in self.browse(cr, uid, ids, context=context):
            res.append(self._formation_struct_get(cr, uid, formation, include_childs=include_childs, context=context))            
        return res

    
    _name = "sale.order.formation"
    _columns = {
        "order_id" : fields.many2one("sale.order", "Sale order"),
        "description" : fields.char("Name", size=64, required=True),
        "parent_id" : fields.many2one("sale.order.formation", "Parent"),
        "child_ids" : fields.one2many("sale.order.formation", "parent_id", "Childs"),
        "name" : fields.char("Position", size=4, required=True),
        "complete_pos" : fields.function(_complete_pos, type="char", size=32, string="Complete Position",
                                         store={
                                            "sale.order.formation" : (_relids_order_formation, ["name", "parent_id"],10)
                                        }),
        "line_ids" : fields.one2many("sale.order.line", "formation_id", "Order lines", invisible=True),
        "print_sum" : fields.boolean("Print Sum",help="Print sum on sale order"),
        "print_formation" : fields.boolean("Print",help="Print formation and its position on sale order"),
        "print_optional" : fields.boolean("Print as Optional",help="Print as optional area on sale order (not included within total sum of order)")
    }

    _defaults = {
        "print_sum" : True,
        "print_formation" : True,
        "print_optional" : False
    }
    
    _order = "complete_pos, description"
    
sale_order_formation()

class sale_order(osv.osv):
    
    def copy_data(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}

        formation_ids = default.get("formation_ids")
        
        if not formation_ids:
            default["formation_ids"] = None
            
        return super(sale_order, self).copy_data(cr, uid, oid, default=default, context=context)
    
    _inherit = "sale.order"
    _columns = {
        "formation_ids" : fields.one2many("sale.order.formation", "order_id", string="Order Formations"),
        
    }
    
sale_order()

class sale_order_line(osv.osv):
    
    def copy_data(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}
            
        formation_id = default.get("formation_id")
        if not formation_id:
            default["formation_id"] = None
         
        return super(sale_order_line, self).copy_data(cr, uid, oid, default=default, context=context)
    
    _inherit = "sale.order.line"
    _columns = {
        "formation_id" : fields.many2one("sale.order.formation", "Formation"),
    }
    
    _order = "formation_id, sequence"
    
sale_order_line()