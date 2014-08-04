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

class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
        "order_finished" : fields.boolean("Order finished")
    }
    
    def copy_data(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}
        if not default.has_key("order_finished"):
            default["order_finished"]=False     
        return super(sale_order, self).copy_data(cr, uid, oid, default, context=context)
    
    def finish_order(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { "order_finished" : True }, context)
        return True        
        
sale_order()