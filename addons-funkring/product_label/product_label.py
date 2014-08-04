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

class product_label_wizard(osv.osv_memory):
    
    def do_print(self, cr, uid, ids, *args):
        for wizard in self.browse(cr, uid, ids):                    
            datas = {
                 "ids": [x.id for x in wizard.product_ids],
                 "model": "product.product"    
            }
            return {
                "type": "ir.actions.report.xml",
                "report_name": "product.product_label",
                "datas": datas
            }    
    
    _columns = {
        "product_ids" : fields.many2many("product.product", "product_label_wizard_rel", "wizard_id", "product_id", "Products"),
    }
    _name = "product.product_label_wizard"
    _description = "Product Label Wizard"
product_label_wizard()