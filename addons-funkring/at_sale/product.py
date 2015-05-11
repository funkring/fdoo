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

class product_product(osv.osv):

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(product_product,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type=="search":
            shop_id =   context.get("shop",None)
            if shop_id:
                fields=res.get('fields',None)
                if fields:
                    field_categ_id =  fields.get('categ_id',None)
                    if field_categ_id:
                        shop_obj = self.pool.get("sale.shop")
                        category_obj  = self.pool.get("product.category")
                        category_ids = shop_obj.get_category_ids(cr,uid,shop_id)
                        if category_ids:
                            categories = category_obj.browse(cr,uid,category_ids,context)
                            category_select = []
                            for category in categories:
                                category_select.append((category.id,category.name))
                            field_categ_id["selection"] = category_select

        return res

    def onchange_brutto_price(self, cr, uid, ids, brutto_price, taxes_id, company_id, context=None):
        res = {
           "value" : {}
        }

        tax_obj = self.pool.get("account.tax")
        cur_obj = self.pool.get("res.currency")
        company_obj = self.pool.get("res.company")

        price = brutto_price
        taxes_list = taxes_id[0][2]
        if taxes_list:
            price_list = tax_obj.compute_inv(cr, uid, tax_obj.browse(cr, uid, taxes_list), price, 1)
            if price_list:
                price = price_list[0]["price_unit"]
        currency_id = company_obj.browse(cr, uid, company_id).currency_id
        if currency_id:
            res["value"]["lst_price"] = cur_obj.round(cr, uid, currency_id, price)
        else:
            res["value"]["lst_price"] = price

        return res



    _inherit = "product.product"

class product_template(osv.osv):

    _inherit = "product.template"

    def onchange_brutto_price(self, cr, uid, ids, brutto_price, taxes_id, company_id, context=None):
        res = {
           "value" : {}
        }

        tax_obj = self.pool.get("account.tax")
        cur_obj = self.pool.get("res.currency")
        company_obj = self.pool.get("res.company")

        price = brutto_price
        taxes_list = taxes_id[0][2]
        if taxes_list:
            price_list = tax_obj.compute_inv(cr, uid, tax_obj.browse(cr, uid, taxes_list), price, 1)
            if price_list:
                price = price_list[0]["price_unit"]
        currency_id = company_obj.browse(cr, uid, company_id).currency_id
        if currency_id:
            res["value"]["list_price"] = cur_obj.round(cr, uid, currency_id, price)
        else:
            res["value"]["list_price"] = price

        return res

    def _calculate_price(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        tax_obj = self.pool.get("account.tax")
        cur_obj = self.pool.get("res.currency")

        for product in self.browse(cr, uid, ids, context=context):
            price = product.list_price
            tax_ids = product.taxes_id
            if tax_ids:
                price = tax_obj.compute_all(cr, uid, tax_ids, price, 1)["total_included"]
            if product.company_id and product.company_id.currency_id:
                cur = product.company_id.currency_id
                res[product.id] = cur_obj.round(cr, uid, cur, price)
            else:
                res[product.id] = price

        return res


    _columns = {
        "brutto_price" : fields.function(_calculate_price, type="float", string="Brutto Price",
                                         help="The brutto price is based on the given tax."),
    }

