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


from openerp.addons.at_account.report import account_invoice_report

class Parser(account_invoice_report.Parser):
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
      
    def _load_objects(self, cr, uid, ids, report_xml, context):
        invoice_ids = []
        for order in self.pool.get("pos.order").browse(cr, uid, ids, context=context):
            if order.invoice_id:
                invoice_ids.append(order.invoice_id.id)
        return self.pool.get("account.invoice").browse(cr, uid, invoice_ids, context=context)   