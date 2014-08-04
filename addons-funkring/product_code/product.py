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

class product_product(osv.osv):
    
    _inherit="product.product"
    
    _columns = {
        "code_value" : fields.char("Scan code", size=128,select=True),
        "code_profile_id" : fields.many2one("product.code.profile", "Scan profile",select=True)
    }

class product_code_profile(osv.osv):
    
#    def _check_length_pos(self, cr, uid, ids, context=None):
#        for product_code in self.browse(cr, uid, ids):
#            if ((product_code.code_length + product_code.price_length + product_code.amount_length) > product_code.length or \
#                product_code.code_pos > product_code.length or
#                product_code.price_pos > product_code.length or
#                product_code.amount_pos > product_code.length or
#                product_code.amount_post_decimal_pos > product_code.length or
#                product_code.price_post_decimal_pos > product_code.length ):
#                return False
#        return True
    
    _name="product.code.profile"
#    _constraints = [
#        (_check_length_pos,"Wrong Input! Please check if the length and the position matches with each other.",["length", "code_pos", "code_length", "price_pos", 
#                                                                           "price_length", "amount_pos", "amount_length"])
#    ] 
    
    _columns = {
        "name" : fields.char("Name", size=128, required=True),
        "length" : fields.integer("Length", required=True),
        "code_pos" : fields.integer("Code Position"),
        "code_length" : fields.integer("Code Length"),
        "price_pos" : fields.integer("Price Position"),
        "price_length" : fields.integer("Price Length"),
        "price_post_decimal_pos" : fields.integer("Price Post Decimal Position"),
        "price_post_decimal_length" : fields.integer("Price Post Decimal Length"),
        "amount_pos" : fields.integer("Amount Position"),
        "amount_length" : fields.integer("Amount Length"),
        "amount_post_decimal_pos" : fields.integer("Amount Post Decimal Position"),
        "amount_post_decimal_length" : fields.integer("Amount Post Decimal Length")
    }
