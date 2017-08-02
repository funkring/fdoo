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
from openerp.tools.translate import _

class sale_order(osv.Model):

    def action_cancel(self, cr, uid, ids, context=None):
        try:
            res = True
            with cr.savepoint():
                res = super(sale_order, self).action_cancel(cr, uid, ids, context=context)
            return res
        except Exception:
            return {
                "type": "ir.actions.act_window",
                "display_name": _("Cancel Order"),
                "view_type": "form",
                "view_mode": "form",
                "res_model": "sale.order.cancel.wizard",         
                "nodestroy": True,   
                "target": "new"
            }

    _inherit = "sale.order"
