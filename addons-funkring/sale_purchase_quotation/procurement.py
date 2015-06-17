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

class procurement_order(osv.Model):
    
    def _get_po_line_values_from_proc(self, cr, uid, procurement, partner, company, schedule_date, context=None):
        res = super(procurement_order,self)._get_po_line_values_from_proc(cr, uid, procurement, partner, company, schedule_date, context=context)
        sale_line = procurement.sale_line_id
        if sale_line:
            supplier = sale_line.supplier_id
            supplier_line_obj = self.pool["sale.line.supplier"]            
            if supplier:
                supplier_line_id = supplier_line_obj.search_id(cr, uid, [("line_id","=",sale_line.id),("partner_id","=",supplier.id)], context=context)
                supplier_line = supplier_line_obj.browse(cr, uid, supplier_line_id, context=context)
                if supplier_line.price:
                    res["price_unit"] = supplier_line.price
        return res

    _inherit = "procurement.order"
