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

class product_template(osv.Model):
    
    def _get_account_income_standard(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context):
            account = product.property_account_income
            if not account:
                account = product.categ_id.property_account_income_categ
            if account:
                res[product.id]=account.id
            else:
                res[product.id]=None
        return res

    def _get_account_expense_standard(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for product in self.browse(cr, uid, ids, context):
            account = product.property_account_expense
            if not account:
                account = product.categ_id.property_account_expense_categ
            if account:
                res[product.id]=account.id
        return res
    
    _inherit = "product.template"
    _columns = {
        "account_income_standard_id" : fields.function(_get_account_income_standard,method=True,
                                                    string="Standard income account",type="many2one",relation="account.account"),
        "account_expense_standard_id" : fields.function(_get_account_expense_standard,method=True,
                                                    string="Standard expense account",type="many2one",relation="account.account")

    }