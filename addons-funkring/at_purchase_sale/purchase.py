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

from openerp.osv import fields,osv

class purchase_order(osv.osv):
    _columns = {             
        "supplier_ships" : fields.boolean("Supplier Ships",states={"confirmed":[("readonly",True)], "approved":[("readonly",True)],"done":[("readonly",True)]})
    }
    _inherit = "purchase.order"


class purchase_order_line(osv.osv):      
           
    def _delivery_address_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for line in self.browse(cr, uid, ids):
            dest_partner = line.dest_address_id
            shop = line.shop_id
            if dest_partner:
                res[line.id] = dest_partner.id
            elif shop:
                warehouse = shop.warehouse_id
                company = shop.company_id
                if warehouse and warehouse.partner_id:
                    res[line.id]=warehouse.partner_id.id
                elif company and company.partner_id:
                    res[line.id]=company.partner_id.id
        return res
            
    def _client_order_ref(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT pl.id, s.client_order_ref "
                   " FROM purchase_order_line pl "
                   " INNER JOIN stock_move m ON m.id = pl.move_dest_id "
                   " INNER JOIN sale_order_line sl ON sl.id = m.sale_line_id "
                   " INNER JOIN sale_order s ON s.id = sl.order_id "
                   " WHERE pl.id IN %s "
                   , (tuple(ids),) )
        
        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res
    
    _inherit = "purchase.order.line"
    _columns = {
        "sale_order_line_id" : fields.related("move_dest_id","sale_line_id",type="many2one",relation="sale.order.line", string="Sale Order Line",readonly=True,store=True),
        "sale_order_id" : fields.related("sale_order_line_id","order_id",type="many2one",relation="sale.order", string="Sale Order",readonly=True,store=True,select=True ),
        "dest_address_id" : fields.related("order_id", "dest_address_id", type="many2one", relation="res.partner", string="Destination Address",readonly=True, store=True, select=True),
        "delivery_address_id" : fields.function(_delivery_address_id, type="many2one", obj="res.partner", string="Delivery Address", readonly=True, method=True),
        "supplier_ships" : fields.related("order_id", "supplier_ships", type="boolean",string="Supplier Ships",readonly=True,select=True,store=True),
        "shop_id" : fields.related("sale_order_id","shop_id",type="many2one",relation="sale.shop",string="Shop",readonly=True,store=True,select=True),        
        "client_order_ref" : fields.function(_client_order_ref,type="char",size=64, string="Customer Reference",readonly=True,store=True,select=True)
    }                        
