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

from openerp.osv import osv

class stock_partial_picking(osv.osv_memory):
    
    def default_get(self, cr, uid, fields, context=None):       
        if context is None:
            context = {}
        #
        res = super(stock_partial_picking, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        #
        if picking_ids:
            picking_id, = picking_ids
            only_assigned = context.get("only_assigned")
            move_line_ids = context.get("move_line_ids")
    
            if only_assigned or move_line_ids:
                picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
                moves = []
                for m in picking.move_lines:                
                    if m.state in ("done","cancel") \
                        or (only_assigned and m.state == "assigned") \
                        or (move_line_ids and m.id in move_line_ids):
                        continue
                    moves.append(self._partial_move_for(cr, uid, m))
                res.update(move_ids=moves)
                
        return res

    _inherit = "stock.partial.picking"
