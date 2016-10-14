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

from openerp.osv import fields, osv

class sale_order(osv.osv):
    
    def action_cancel(self, cr, uid, ids, context=None):
        """called when orders are canceled"""
        commission_line_obj = self.pool.get("commission.line")
        commission_line_ids = commission_line_obj.search(cr,uid,[("order_line_id.order_id","in",ids)])        
        commission_line_obj.unlink(cr, uid, commission_line_ids)                        
        return super(sale_order,self).action_cancel(cr, uid, ids, context)
    
    _inherit = "sale.order"
