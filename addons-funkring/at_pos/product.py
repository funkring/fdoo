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
from at_base import format

class product_product(osv.osv):
    
    def _price_brutto(self,cr,uid,ids,field_name,arg,context=None):      
        if not context:
            context = {}    
        pricelist_id = self.pool.get("pos.order")._select_pricelist(cr,uid,context)
        if not pricelist_id:
            return 0.0        
        pos_order_line_obj = self.pool.get("pos.order.line")        
        res = dict.fromkeys(ids)
        for oid in ids:
            res[oid]=pos_order_line_obj.price_by_product(cr,uid,None,pricelist_id,oid,1)
        return res
    
    def _info_line(self, cr, uid, ids, field_name, arg, context=None):                                    
        if not context:
            context = {}    
        
        res = {}
        curText = ""
                        
        pricelist_id = self.pool.get("pos.order")._select_pricelist(cr,uid,context)
        if pricelist_id:
            pricelist = self.pool.get("product.pricelist").browse(cr,uid,pricelist_id,context)
            if pricelist.currency_id:
                curText = pricelist.currency_id.symbol
                
        lf = format.LangFormat(cr,uid,context,dp="Point Of Sale")
        for product in self.browse(cr, uid, ids, context):
            res[product.id] = lf.formatLang(product.price_brutto) + " " + curText + " per " + product.uom_id.name
                    
        return res
                  
    _inherit = "product.product"
    _columns = {
        "price_brutto" : fields.function(_price_brutto, string='Brutto Unit Price'),
        "info_line" : fields.function(_info_line, type="char", string="Info Line"),
        "needs_measure" : fields.boolean("Needs Measurement",help="This Article needs measurement before it could be sold"),
        "has_sn" : fields.boolean("Serial Number",help="Has Serialnumber? This is an article like voucher with an serial number"), 
        "cashbox_report_detail" : fields.boolean("Show in Cashbox Report",help="Show as Extra Line in Cashbox Report"),
        "is_detail_product" : fields.boolean("Is detail Product")
    }
    
product_product()
    