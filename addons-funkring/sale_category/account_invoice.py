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

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def _sale_category(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids)
        order_line_obj = self.pool.get("sale.order.line")
        for invoice in self.browse(cr, uid, ids):
            if invoice.custom_sale_category_id:
                res[invoice.id] = invoice.custom_sale_category_id.id
            else:
                invoice_line_ids = []
                for line in invoice.invoice_line:
                    invoice_line_ids.append(line.id)
                if invoice_line_ids:
                    cr.execute("SELECT order_line_id FROM sale_order_line_invoice_rel ir"
                               " WHERE ir.invoice_id in %s GROUP BY 1", (tuple(invoice_line_ids),))
                    order_line_ids = [r[0] for r in cr.fetchall()]
                    order_id = None
                    for order_line in order_line_obj.browse(cr, uid, order_line_ids):
                        if (order_id == None or order_id == order_line.order_id.id) and order_line.order_id.sale_category_id:
                            res[invoice.id] = order_line.order_id.sale_category_id.id
                        else:
                            res[invoice.id] = None
                            break
                        order_id = order_line.order_id.id

        return res

    _columns = {
        "sale_category_id" : fields.function(_sale_category, type="many2one", obj="sale.category", store=True, method=True, string="Category"),
        "custom_sale_category_id" : fields.many2one("sale.category", "Custom category"),
    }
