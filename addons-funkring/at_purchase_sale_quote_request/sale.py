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
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from at_base import util

class sale_order(osv.osv):
        
    def _quote_rate(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        res_count_all = {}
        res_count_finished = {} 
              
        cr.execute("SELECT origin_sale_order_id,count(id) FROM purchase_order_line WHERE origin_sale_order_id IN %s GROUP BY 1",(tuple(ids),))
        for row in cr.fetchall():
            res_count_all[row[0]]=row[1] 
        
        cr.execute("SELECT origin_sale_order_id,count(id) FROM purchase_order_line WHERE origin_sale_order_id IN %s AND supplier_unit_price > 0 GROUP BY 1",(tuple(ids),))
        for row in cr.fetchall():
            res_count_finished[row[0]]=row[1]
             
        for oid in ids:
            countAll = float(res_count_all.get(oid,0.0))
            countFinished = float(res_count_finished.get(oid,0.0))
            if not countAll or countAll == countFinished:
                res[oid]=100.0
            else:
                res[oid]=countAll / 100.0 * countFinished
        return res
        
    def _relids_purchase_order_line(self, cr, uid, ids, context=None):
        cr.execute("SELECT origin_sale_order_id FROM purchase_order_line WHERE purchase_order_line.id IN %s GROUP BY 1",(tuple(ids),))
        res =[]
        for row in cr.fetchall():
            res.append(row[0])
        return res
            
    _inherit = "sale.order"    
    _columns = {                
        "quote_rate" : fields.function(_quote_rate,string="Quote Requests",store={
                            "purchase.order.line" : (_relids_purchase_order_line,["supplier_unit_price"],10)
                        })
    }


class sale_order_line(osv.osv):
        
    def request_quote(self, cr, uid, ids, context=None):
        purchaseObj = self.pool.get("purchase.order.line")       
        accountFiscalPosObj = self.pool.get("account.fiscal.position")
        partnerObj = self.pool.get("res.partner")
        pricelistObj = self.pool.get("product.pricelist")        
        procurementObj = self.pool.get("procurement.order")  
        
        for line in self.browse(cr, uid, ids, context):            
            preferredSeller = line.preferred_seller_id
            product = line.product_id
            if line.state == "draft" and preferredSeller and product and product.product_tmpl_id.type in ("product","consu"):
                partner = preferredSeller.name
                purchaseLinesIds = purchaseObj.search(cr,uid,[("origin_sale_order_line_id","=",line.id),("partner_id","=",partner.id)])
                if not purchaseLinesIds:
                    #get company
                    company = line.order_id.company_id
                    
                    #get address
                    addressId = partnerObj.address_get(cr, uid, [partner.id], ['delivery'])['delivery']
                    
                    #get notes
                    notes = [] 
                    if product.partner_ref != line.name:
                        notes.append(line.name)
                    if product.description_purchase:
                        notes.append(product.description_purchase)
                    if line.notes:
                        notes.append(line.notes)
                    if line.procurement_note:
                        notes.append(line.procurement_note)                                
                    notes = notes and "\n\n".join(notes) or None  
                                                                                   
                    #calculate date 
                    date_start = datetime.now()
                    date_planned = date_start + relativedelta(days=line.delay or 0.0)   
                    date_planned = date_planned - timedelta(days=company.security_lead)
                    
                    if company.calendar_id:
                        nonworking_days = self.pool.get("resource.calendar").nonworking_day_count(cr,uid,company.calendar_id.id,date_start,date_planned)
                        if nonworking_days:
                            date_planned += relativedelta(days=nonworking_days)
                    
                    date_planned = (date_planned - relativedelta(days=company.po_lead))             
                    date_planned = util.timeToStr(date_planned)
                   
                    #price                  
                    pricelist = partner.property_product_pricelist_purchase       
                    price = pricelistObj.price_get(cr, uid, [pricelist.id], product.id, 
                                                   line.product_uom_qty, partner.id, 
                                                   {"uom": line.product_uom.id})[pricelist.id]
                   
                    #line
                    po_line = {
                        "origin_sale_order_line_id" : line.id,
                        "name": product.partner_ref, 
                        "product_qty": line.product_uom_qty,
                        "product_id": product.id,
                        "product_uom": line.product_uom.id,
                        "price_unit": price,
                        "date_planned": date_planned,
                        "notes": notes,
                        "priority" : line.priority
                    }
                        
                    taxes_ids = product.product_tmpl_id.supplier_taxes_id
                    taxes = accountFiscalPosObj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
                    po_line.update({
                        "taxes_id": [(6,0,taxes)]
                    })
                    
                    location = line.order_id.shop_id.warehouse_id.lot_stock_id
                    po_order = {                        
                        "origin": line.order_id.name,                        
                        "partner_id": partner.id,
                        "partner_address_id": addressId,
                        "location_id": location.id,
                        "pricelist_id": pricelist.id,
                        "order_line": [(0,0,po_line)],
                        "company_id": company.id,
                        "fiscal_position": partner.property_account_position and partner.property_account_position.id or False,
                        "supplier_ships" : line.supplier_ships
                    }                
                    #
                    if line.supplier_ships:
                        po_order["dest_address_id"]=line.order_id.partner_shipping_id.id
                    #
                    procurementObj.create_procurement_purchase_order(cr,uid,po_order,po_line,context=context)
        return True
    
    
    def copy_data(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}
        default["purchase_request_ids"] = []            
        return super(sale_order, self).copy_data(cr, uid, oid, default, context=context)
    
    
    _inherit = "sale.order.line"    
    _columns = {
        "purchase_request_ids" : fields.one2many("purchase.order.line","origin_sale_order_line_id",string="Purchase Requests",readonly=True,states={"draft": [("readonly", False)]})
     }
