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
from openerp import api

class account_invoice_line(osv.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def product_id_change(self, product_id, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):
               
        res = super(account_invoice_line,self).product_id_change(product_id, 
                                                                  uom_id, 
                                                                  qty=qty, 
                                                                  name=name, 
                                                                  type=type, 
                                                                  partner_id=partner_id, 
                                                                  fposition_id=fposition_id, 
                                                                  price_unit=price_unit, 
                                                                  currency_id=currency_id, 
                                                                  company_id=company_id)
        values = res["value"]
        
        # check for category price
        if not price_unit and product_id and self.env["academy.course.product"].search([("product_id","=",product_id)]):            
            product = self.env["product.product"].browse(product_id)
            if uom_id and uom_id != product.uom_id.id:
                uom = self.env["product.uom"].browse(uom_id)
                if uom.list_price:
                    values["price_unit"] = uom.list_price
        
        return res
                    
        