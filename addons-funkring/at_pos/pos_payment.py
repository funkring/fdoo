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
import decimal_precision as dp

class pos_order_payment(osv.osv):
    
    _columns = {
        "name" : fields.char("Name",size=32),
        "order_id" : fields.many2one("pos.order","Order",ondelete="cascade",required=True,select=True),
        "type" : fields.selection([("cash","Bar"),("balance","Balance"),("voucher","Gutschein")],"Type",required=True,select=True),        
        "amount" : fields.float("Amount",digits_compute=dp.get_precision("Point Of Sale")),
        "balance" : fields.float("Balance",digits_compute=dp.get_precision("Point Of Sale")),        
        "statement_line_id" : fields.many2one("account.bank.statement.line","Statement Line",ondelete="cascade",select=True)
    }
    _name="pos.order.payment"
    _description="POS Order Payment"
pos_order_payment()