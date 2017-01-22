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

class product_commission(osv.osv):
    
    _name="commission_product.commission"
    _description="Commission"
    _rec_name = "product_id"
    _columns = {
        "product_id" : fields.many2one("product.product","Product",required=True,select=True),
        "partner_id" : fields.many2one("res.partner","Partner",required=True),
        "commission_percent" : fields.float("Commission %"),
        "property_commission_product" : fields.property(type="many2one",
                                                        relation="product.product",
                                                        string="Invoice Product"
                                                        ),
        "property_analytic_journal" : fields.property(type="many2one",
                                                      relation="account.analytic.journal",
                                                      string="Commission Journal")
    }
    
    
class product_template(osv.osv):
    
    _inherit = "product.template"
    _columns = {
        "commission_ids" : fields.related("product_variant_ids", "commission_ids", obj="commission_product.commission", type="one2many", string="Commission")
    }
    
    
class product_product(osv.osv):
       
    _inherit = "product.product"
    _columns = {
        "commission_ids" : fields.one2many("commission_product.commission","product_id","Commission")
    }
