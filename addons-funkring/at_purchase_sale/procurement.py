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

from openerp.osv import fields,osv

class procurement_order(osv.osv):   
    
    def create_procurement_purchase_order(self, cr, uid, procurement, po_vals, line_vals, context=None):
        po_vals["supplier_ships"]=procurement.supplier_ships
        if procurement.supplier_ships:
            po_vals["dest_address_id"]=procurement.dest_address_id and procurement.dest_address_id.id or None
        return super(procurement_order,self).create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context=context)
     
    _inherit = "procurement.order"        
    _columns = {
        "supplier_ships" : fields.boolean("Supplier Ships"),        
    }