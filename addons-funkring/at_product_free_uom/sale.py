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

from openerp.osv import osv


class sale_order_line(osv.osv):
    
    def product_id_change_at(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, shop_id=None, product_change=False):
        
        res = super(sale_order_line,self).product_id_change_at(cr,uid,ids,pricelist,product,
                                                                  qty=qty,uom=uom,qty_uos=qty_uos,uos=uos,name=name,
                                                                  partner_id=partner_id,lang=lang,
                                                                  update_tax=update_tax,date_order=date_order,
                                                                  packaging=packaging,fiscal_position=fiscal_position,
                                                                  flag=flag,
                                                                  shop_id=shop_id,
                                                                  product_change=product_change) 
        if product:
            product_obj = self.pool.get("product.product")
            cur_product = product_obj.browse(cr,uid,product)
            if cur_product.free_uom:
                domain = res.get("domain",{})    
                domain.update({"product_uom" : []})
                res["domain"]= domain                
                if uom and res["value"].has_key("product_uom"):
                    del res["value"]["product_uom"]                
                
        return res
        
    
    def product_uom_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):

        cur_product = None
        if product:
            product_obj = self.pool.get("product.product")
            cur_product = product_obj.browse(cr,uid,product)
            if cur_product.free_uom:
                return {}
        
        return super(sale_order_line,self).product_uom_change(cr,uid,ids,pricelist,product,
                                                                  qty=qty,uom=uom,qty_uos=qty_uos,uos=uos,name=name,
                                                                  partner_id=partner_id,lang=lang,
                                                                  update_tax=update_tax,date_order=date_order)
        
    _inherit = "sale.order.line"   
sale_order_line()
