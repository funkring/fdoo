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

class account_invoice_refund(osv.osv_memory):
  _inherit = "account.invoice.refund"

  def _get_reason(self, cr, uid, context=None):
    active_id = context and context.get('active_id', False)
    if active_id:
        inv = self.pool.get('account.invoice').browse(cr, uid, active_id, context=context)
        refund_reason = inv.number or inv.internal_number or inv.name or ''
        if refund_reason:
          return _("Refund %s") % refund_reason
    return ''
  
  _defaults = {
    "description": _get_reason
  }