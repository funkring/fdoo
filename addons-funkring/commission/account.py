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

class account_invoice(osv.osv):
    
    def _replace_invoice_ids_with_id(self, cr, uid, ids, oid, context=None):
        super(account_invoice,self)._replace_invoice_ids_with_id(cr, uid, ids, oid, context)
        commission_line_obj = self.pool.get("commission.line")
        related_ids = commission_line_obj.search(cr,uid,[("invoiced_id","in",ids)])
        commission_line_obj.write(cr, uid, related_ids, {"invoiced_id" : oid}, context)
            
    def action_cancel(self, cr, uid, ids, *args, **kwargs):
        commission_line_obj = self.pool.get("commission.line")
        commission_line_ids = commission_line_obj.search(cr,uid,[("invoice_line_id.invoice_id","in",ids)])        
        commission_line_obj.unlink(cr, uid, commission_line_ids)                        
        return super(account_invoice,self).action_cancel(cr, uid, ids, *args, **kwargs)
    
    _inherit = "account.invoice"


class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    _columns = {
        "commission_line_ids" : fields.many2many("commission.line", "commission_invoice_line_rel", "invoice_line_id", "commission_line_id", "Commission Lines"),
    } 
    
