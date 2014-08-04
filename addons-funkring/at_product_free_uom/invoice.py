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

class invoice_line(osv.osv):
    
    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, currency_id=False, context=None):
        res = super(invoice_line,self).product_id_change(cr,uid,ids,product,uom,qty,name,type,partner_id,fposition_id,price_unit,address_invoice_id,currency_id,context)
        if product:
            product_obj = self.pool.get("product.product")
            cur_product = product_obj.browse(cr,uid,product)
            if cur_product.free_uom:
                domain = res.get("domain",{})    
                domain.update({"uos_id" : []})
                res["domain"]= domain                
                if uom and res["value"].has_key("uos_id"):
                    del res["value"]["uos_id"]
        return res
        
    
    def uos_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, currency_id=False, context=None):
        cur_product = None
        if product:
            product_obj = self.pool.get("product.product")
            cur_product = product_obj.browse(cr,uid,product)
            if cur_product.free_uom:
                return {}
            
        return super(invoice_line,self).uos_id_change(cr,uid,ids,product,uom, \
                                        qty=qty,name=name,type=type,partner_id=partner_id,fposition_id=fposition_id, \
                                        price_unit=price_unit,address_invoice_id=address_invoice_id,currency_id=currency_id,context=context)
        
    
    _inherit = "account.invoice.line"    
invoice_line()