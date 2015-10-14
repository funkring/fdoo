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

from openerp import models, fields, api, _

class ProductChange(models.TransientModel):
    
    _name = "at_sale.product_change_wizard"
    _description = "Product Change"
    
    product_ids = fields.Many2many("product.product","rel_wizard_product_change_product","wizard_id","product_id",string="Products")
    supplier_ids = fields.Many2many("res.partner","rel_wizard_product_change_supplier","wizard_id","supplier_id",string="Suppliers")
    supplier_replace = fields.Boolean("Replace Suppliers")
    
    
    @api.multi
    def action_change(self):       
        for wizard in self:
            suppliers = wizard.supplier_ids
            #product_ids = [p.id for p in wizard.product_ids]
            if suppliers:
                supplier_obj = self.env["product.supplierinfo"]
                
                for product in wizard.product_ids:
                    cur_partner_ids = set()
                    for seller in product.seller_ids:
                        if wizard.supplier_replace:
                            seller.unlink()
                        else:
                            cur_partner_ids.add(seller.name.id)
                
                    # add new suppliers
                    for partner in suppliers:
                        if not partner.id in cur_partner_ids:
                            supplier_obj.create({
                                "product_tmpl_id" : product.product_tmpl_id.id,
                                "name"  : partner.id
                            })
                    
             
        return { "type" : "ir.actions.act_window_close" }
    