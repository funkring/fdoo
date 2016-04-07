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
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID

class product_product(osv.osv):

    def onchange_brutto_price(self, cr, uid, ids, brutto_price, taxes_id, company_id, context=None):
        return self._onchange_price(cr, uid, ids, brutto_price, taxes_id, company_id, True, price_field="lst_price", context=context)
       
    def onchange_netto_price(self, cr, uid, ids, brutto_price, taxes_id, company_id, context=None):
        return self._onchange_price(cr, uid, ids, brutto_price, taxes_id, company_id, False, price_field="lst_price", context=context)

    _inherit = "product.product"


class product_template(osv.osv):

    def _onchange_price(self, cr, uid, ids, price, taxes_id, company_id, tax_included, price_field="list_price", context=None):
        res = {
           "value" : {}
        }

        tax_obj = self.pool.get("account.tax")
        cur_obj = self.pool.get("res.currency")
        company_obj = self.pool.get("res.company")

        # get company
        if not company_id:
            company_id = company_obj._company_default_get(cr, uid, "product.template", context=context)

        # get taxes
        taxes_list = taxes_id[0][2]
        taxes = None
        if taxes_list:
            taxes = tax_obj.browse(cr, uid, taxes_list)
            if taxes:
                taxes = [t for t in taxes if not t.company_id or t.company_id.id == company_id]
                             
        # calc other         
        brutto = netto = price
        if taxes:
            price_all = None
            if tax_included:
                price_all = tax_obj.compute_full(cr, uid, taxes, price, 1, force_included=True)
            else:
                price_all = tax_obj.compute_full(cr, uid, taxes, price, 1, force_excluded=True)

            brutto = price_all["total_included"]
            netto = price_all["total"]
            price = tax_obj.compute_full(cr, uid, taxes, netto, 1, netto_to_price=True)["total_included"]
            
        # round
        currency_id = company_obj.browse(cr, uid, company_id).currency_id
        if currency_id:
            price = cur_obj.round(cr, uid, currency_id, price)
            brutto = cur_obj.round(cr, uid, currency_id, brutto)
            netto = cur_obj.round(cr, uid, currency_id, netto)
            
        # set netto or brutto
        if tax_included:
            res["value"]["netto_price"] = netto                        
        else:
            res["value"]["brutto_price"] = brutto

        res["value"][price_field] = price        
        return res

    def onchange_brutto_price(self, cr, uid, ids, brutto_price, taxes_id, company_id, context=None):
        return self._onchange_price(cr, uid, ids, brutto_price, taxes_id, company_id, True, context=context)
       
    def onchange_netto_price(self, cr, uid, ids, brutto_price, taxes_id, company_id, context=None):
        return self._onchange_price(cr, uid, ids, brutto_price, taxes_id, company_id, False, context=context)
    
    def _calculate_price(self, cr, uid, ids, field_names, arg, context=None):
        res = dict.fromkeys(ids)
        tax_obj = self.pool.get("account.tax")
        cur_obj = self.pool.get("res.currency")

        for product in self.browse(cr, SUPERUSER_ID, ids, context=context):
            price = netto = brutto = product.list_price
            tax_ids = product.taxes_id
            if tax_ids:
                price_all = tax_obj.compute_all(cr, SUPERUSER_ID, tax_ids, price, 1)
                brutto = price_all["total_included"]
                netto = price_all["total"]                
            if product.company_id and product.company_id.currency_id:
                cur = product.company_id.currency_id     
                brutto =  cur_obj.round(cr, SUPERUSER_ID, cur, brutto)
                netto =  cur_obj.round(cr, SUPERUSER_ID, cur, netto)                
            
            res[product.id] = {
                "brutto_price" : brutto,
                "netto_price" : netto
            }                        
        return res

    _inherit = "product.template"
    _columns = {
        "brutto_price" : fields.function(_calculate_price, type="float", string="Brutto Price",
                                         help="The brutto price is based on the given tax.", multi="_calculate_price"),
                
        "netto_price" : fields.function(_calculate_price, type="float", string="Netto Price",
                                         help="The netto price without tax.", multi="_calculate_price")
    }

