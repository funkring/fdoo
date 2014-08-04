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

from openerp.osv import osv
from openerp.tools.translate import _

class account_invoice(osv.osv):
    
    def action_number(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids, context):
            for line in invoice.invoice_line:
                product = line.product_id
                if product and not line.invoice_line_tax_id:
                    raise osv.except_osv(_("Warning"), _("There is an product but no taxes!\nLine: %s") % (line.name,))
        super(account_invoice,self).action_number(cr,uid,ids,context)
         
    _inherit="account.invoice"
account_invoice()