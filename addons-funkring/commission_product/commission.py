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

from openerp.osv import osv
from openerp import api
from openerp.tools.translate import _

class commission_line(osv.Model):
    
    @api.cr_uid_context
    def _validate_product_commission(self, cr, uid, values, obj=None, company=None, context=None):
      return values
    
    @api.cr_uid_context
    def _get_product_commission(self, cr, uid, name, product, qty, netto, date, defaults=None, obj=None, company=None, period=None, context=None):
        res = []
        commission_obj = self.pool["commission_product.commission"]
        period_obj = self.pool["account.period"]
        commission_ids = commission_obj.search(cr, uid, [("product_id", "=", product.id)], context=context)
        for commission in commission_obj.browse(cr, uid, commission_ids, context=context):
            factor = (commission.commission_percent / 100.0)*-1
            
            period_id = period and period.id or None
            if not period_id:
                period_id = period_obj.find(cr, uid, dt=date, context=context)[0]
            
            if commission.commission_percent:
                entry = {}
                if defaults:
                    entry.update(defaults)
                entry.update({
                    "date": date,
                    "name": _("Product Commission: %s") % self._short_name(name),
                    "unit_amount": qty,
                    "amount": netto*factor,
                    "base_commission" : commission.commission_percent,
                    "total_commission" : commission.commission_percent,
                    "product_id": commission.property_commission_product.id,
                    "product_uom_id": commission.property_commission_product.uom_id.id,
                    "general_account_id": commission.property_commission_product.account_income_standard_id.id,
                    "journal_id": commission.property_analytic_journal.id,
                    "partner_id" : commission.partner_id.id,
                    "user_id" : uid,
                    "period_id" : period_id,
                    "price_sub" : netto
                })
                entry = self._validate_product_commission(self, cr, uid, entry, obj=obj, company=company, context=context)
                if entry:
                  res.append(entry)
                
        return res
    
    _inherit = "commission.line"
    
    
