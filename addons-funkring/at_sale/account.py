# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

#############################################################################\
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

class account_invoice(osv.osv):
    _columns = {
        "sale_order_ids" : fields.many2many("sale.order","sale_order_invoice_rel","invoice_id","order_id","Orders",readonly=True),
    }
    _inherit = "account.invoice"


class account_invoice_line(osv.osv):
    
    def _order_info(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids)               
        for invoice_line in self.browse(cr, uid, ids):
            for order_line in invoice_line.sale_order_line_ids:
                order = order_line.order_id
                infos = []
                if order.name:
                    infos.append(order.name)
                if order.client_order_ref:
                    infos.append(order.client_order_ref)
                res[invoice_line.id] = " / ".join(infos)  
        return res
    
    _inherit = "account.invoice.line"
    _columns = {
        "order_info" : fields.function(_order_info, type="text", string="Order Info"),
        "sale_order_line_ids" : fields.many2many("sale.order.line", "sale_order_line_invoice_rel", "invoice_id", "order_line_id", "Sale Order Lines")
    }
