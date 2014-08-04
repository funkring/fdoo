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

from openerp.osv import osv,fields
from at_base import format
from openerp.tools.translate import _


class server_profile(osv.osv):
    
    def _edi_fc_determine_shop_id(self,cr,uid,profile,address_id,direct_delivery=False,context=None):
        shop_id = None
        if address_id:
            address = self.pool.get("res.partner.address").browse(cr, uid, address_id, context)
            country = address.country_id
            if country:
                country_shop_obj = self.pool.get("edi.country.shop")
                ids = country_shop_obj.search(cr,uid,[("server_profile_id","=",profile.id),("country_id","=",country.id)])
                shop_country_mapping = ids and country_shop_obj.browse(cr,uid,ids[0],context) or None
                if shop_country_mapping:
                    if direct_delivery:
                        shop_id = shop_country_mapping.dd_shop_id and shop_country_mapping.dd_shop_id.id or None
                    else:                        
                        shop_id = shop_country_mapping.shop_id and shop_country_mapping.shop_id.id or None
        #
        if not shop_id:
            if profile.shop_id:
                shop_id=profile.shop_id.id
            if direct_delivery and profile.dd_shop_id:
                shop_id=profile.dd_shop_id.id
        #   
        return shop_id
        
    
    def edi_fv_purchase_line_confirm(self,cr,uid,purchase_line_ids,context=None):
        profile = self._profile_get(cr,uid)
        mapped_uid = profile.property_mapped_user.id
        #
        line_obj = self.pool.get("purchase.order.line")
        purchase_line_ids = line_obj.search(cr,mapped_uid,[("id","in",purchase_line_ids)])
        line_obj.confirm(cr,mapped_uid,purchase_line_ids,context)
        return True
    
    def edi_fv_purchase_line_shipped(self,cr,uid,purchase_line_ids,context=None):
        profile = self._profile_get(cr,uid)
        mapped_uid = profile.property_mapped_user.id
        #
        line_obj = self.pool.get("purchase.order.line")
        purchase_line_ids = line_obj.search(cr,mapped_uid,[("id","in",purchase_line_ids)])
        line_obj.confirm_direct_delivery(cr,mapped_uid,purchase_line_ids,context)
        return True
                    
    def edi_fv_recheck_order(self,cr,uid,order_id,context=None):
        profile = self._profile_get(cr,uid)
        system = profile.system_id
        mapped_uid = profile.property_mapped_user.id
        # get order
        sale_order_obj = self.pool.get("sale.order")
        order = sale_order_obj.browse(cr,mapped_uid,order_id,context=context)
        if not order:
            raise osv.except_osv(_("Error"), _("Customer order does not exists"))        
        #recheck again
        transfer_obj = self.pool.get("edi.transfer")
        transfer_obj._call(cr,mapped_uid,system.partner_id.id,sale_order_obj._name,order.id,sale_order_obj._edi_tv_recheck_order)
        return True 
                    
                    
    def edi_fc_order(self,cr, uid, purchases, context=None):
        for purchase in purchases:
            self.edi_fc_purchase(cr, uid, purchase, context)
        return True
    
    
    def edi_fc_recheck_order(self,cr,uid,remote_sale_order_id,purchases,context=None):
        profile = self._profile_get(cr,uid)
        system = profile.system_id
        mapped_uid = profile.property_mapped_user.id
        
        profile_obj = self.pool.get("edi.profile")
        sale_order_obj = self.pool.get("sale.order")
        sale_order_line_obj = self.pool.get("sale.order.line")
        link_obj = self.pool.get("edi.link")
        product_obj = self.pool.get("product.product")
                
        sale_order = None        
        if remote_sale_order_id:
            sale_order_id = link_obj._local_id(cr,mapped_uid,system.id,sale_order_obj._name,remote_sale_order_id)
            sale_order = sale_order_obj.browse(cr,mapped_uid,sale_order_id)
                        
        if not sale_order:
            raise osv.except_osv(_("Error"), _("Sale Order Mapping for Customer Order with ID=%d is lost") % (remote_sale_order_id,))
            
        if len(sale_order.order_line) != len(purchases):
            raise osv.except_osv(_("Error"), _("Sale Order Line Count of Customer Order is not the same"))
        
        for purchase in purchases:
            name = purchase.get("name")           
            remote_sale_order_id = purchase.get("sale_order_id")
            remote_purchase_order_id = purchase.get("order_id")
            remote_purchase_line_id = purchase.get("id")            
            product_id = profile_obj._edi_unpack_product(cr, mapped_uid, system, purchase.get("product"))
            address_id = profile_obj._edi_unpack_address(cr, mapped_uid, system, purchase.get("address"),modify=False)
            product_qty = purchase.get("product_qty",None)
            
            if not name:
                raise osv.except_osv(_("Error"), _("No Name for Purchase Passed")) 
            if not remote_purchase_order_id:
                raise osv.except_osv(_("Error"), _("No Purchase Order ID transfered"))
            if not remote_purchase_line_id:
                raise osv.except_osv(_("Error"), _("No Purchase Line ID transfered"))
            if not address_id:
                raise osv.except_osv(_("Error"), _("Delivery Address invalid for purchase %s") % (name,))
            if not product_id:
                raise osv.except_osv(_("Error"), _("No Product for Purchase %s") % (name,))            
            if not product_qty:
                raise osv.except_osv(_("Error"), _("No Quantity for Purchase %s") % (name,))           
            
            sale_order_line_id = link_obj._local_id(cr,mapped_uid,system.id,"purchase.order.line",remote_purchase_line_id,
                                                local_model=sale_order_line_obj._name)
            
            sale_order_line = sale_order_line_obj.browse(cr,mapped_uid,sale_order_line_id)
            if not sale_order_line:
                raise osv.except_osv(_("Error"), _("Sale Order Line for Customer purchase with name %s was not found") % (name,))
                        
            def product_name(product):
                if product and product.name:
                    if product.default_code:
                        return "[%s] %s" % (product.default_code,product.name)
                    return product.name
                return _("None")
                        
            product_is = product_name(sale_order_line.product_id)
            if sale_order_line.product_id.id != product_id:                
                product_should = product_obj.browse(cr,mapped_uid,product_id)
                product_should = product_name(product_should)
                raise osv.except_osv(_("Error"), _("Customer purchased product %s but in the Order is product %s") % (product_should,product_is))
            
            if sale_order_line.product_uos_qty != product_qty:
                f = format.LangFormat(cr,mapped_uid,dp="Product UoM")
                raise osv.except_osv(_("Error"), _("Product sales quantity for product %s should be %s but is %s ")
                                      % (product_is,f.formatLang(product_qty),f.formatLang(sale_order_line.product_uos_qty)))
                
            if sale_order_line.order_id.partner_shipping_id.id != address_id:
                raise osv.except_osv(_("Error"), _("Partner shipping address is no the same"))
                                
        return True 
                      
    def edi_fc_purchase(self, cr, uid, purchase, context=None):
        profile = self._profile_get(cr,uid)
        system = profile.system_id
        partner = system.partner_id
        mapped_uid = profile.property_mapped_user.id
        
        profile_obj = self.pool.get("edi.profile")
        sale_order_obj = self.pool.get("sale.order")
        sale_order_line_obj = self.pool.get("sale.order.line")
        link_obj = self.pool.get("edi.link")
        

        name = purchase.get("name")
        order_name = purchase.get("order_name")
        sale_order_name = purchase.get("sale_order_name")        
        remote_sale_order_id = purchase.get("sale_order_id")
        remote_purchase_order_id = purchase.get("order_id")
        remote_purchase_line_id = purchase.get("id")
        address_id = profile_obj._edi_unpack_address(cr, mapped_uid, system, purchase.get("address"))
        notes = purchase.get("notes")
        supplier_ships = purchase.get("supplier_ships",False)
        
        product_id = profile_obj._edi_unpack_product(cr, mapped_uid, system, purchase.get("product"))
        product_qty = purchase.get("product_qty",None)
        product_uom_id = profile_obj._edi_unpack_uom(cr, mapped_uid, system, purchase.get("product_uom"))
        
        if not name:
            raise osv.except_osv(_("Error"), _("No Name for Purchase Passed")) 
        if not remote_purchase_order_id:
            raise osv.except_osv(_("Error"), _("No Purchase Order ID transfered"))
        if not remote_purchase_line_id:
            raise osv.except_osv(_("Error"), _("No Purchase Line ID transfered"))
        if not address_id:
            raise osv.except_osv(_("Error"), _("Delivery Address invalid for purchase %s") % (name,))
        if not product_id:
            raise osv.except_osv(_("Error"), _("No Product for Purchase %s") % (name,))            
        if not product_qty:
            raise osv.except_osv(_("Error"), _("No Quantity for Purchase %s") % (name,))            
        
                
        # check if sale order already exists
        sale_order_id = None
        # check sale order link
        if remote_sale_order_id:
            sale_order_id = link_obj._local_id(cr,mapped_uid,system.id,sale_order_obj._name,remote_sale_order_id)
            
        # check purchase order link
        if not sale_order_id:
            sale_order_id = link_obj._local_id(cr,mapped_uid,system.id,"purchase.order",remote_purchase_order_id,
                                               local_model=sale_order_obj._name)
        
        # check sale order line link
        sale_order_line_id = link_obj._local_id(cr,mapped_uid,system.id,"purchase.order.line",remote_purchase_line_id,
                                                local_model=sale_order_line_obj._name)
        if sale_order_line_id:
            sale_order_line = sale_order_line_obj.browse(cr,mapped_uid,sale_order_line_id)
            sale_order_id = sale_order_line.order_id.id
            

        #check sale order        
        if sale_order_id:            
            sale_order = sale_order_obj.browse(cr, mapped_uid, sale_order_id, context)
            if sale_order.state=="draft":
                #check or correct shipping address
                if sale_order.partner_shipping_id.id != address_id:
                    sale_order_obj.write(cr,mapped_uid,sale_order_id,{"partner_shipping_id" : address_id})
            else:
                #create new sale order if it is not draft
                sale_order_id = None 
        
                               
        # create sale order        
        if not sale_order_id:
            sale_order_vals = {
                "partner_id" : partner.id
            }            
            # determine shop
            shop_id = self._edi_fc_determine_shop_id(cr, mapped_uid, profile, address_id, 
                                    direct_delivery=supplier_ships,context=context)            
            #
            if sale_order_name:
                sale_order_vals["client_order_ref"]=sale_order_name
            elif order_name:
                sale_order_vals["client_order_ref"]=order_name
            #
            if shop_id:
                sale_order_vals["shop_id"]=shop_id
                res = sale_order_obj.onchange_shop_id(cr,mapped_uid,[],shop_id)
                sale_order_vals.update(res.get("value"))
                        
            res = sale_order_obj.onchange_partner_id2(cr,mapped_uid,[],partner.id,shop_id)            
            sale_order_vals.update(res.get("value"))     
            if address_id:       
                sale_order_vals["partner_shipping_id"]=address_id       
            sale_order_id = sale_order_obj.create(cr,mapped_uid,sale_order_vals,context)
        
        #
        # create sale order line
        #
        #        
        sale_order = sale_order_obj.browse(cr, mapped_uid, sale_order_id, context)
        #
        # warnings
        if not product_uom_id:
            sale_order_obj.log(cr,mapped_uid,sale_order_id,_("No Uom for Purchase %s passed!") % (name,),warning=True)
        # line
        line_vals = {
            "order_id" : sale_order_id,
            "name" : name,
            "product_id" :  product_id,
            "product_uom_qty" : product_qty,            
        }
        if product_uom_id:
            line_vals["product_uom"]=product_uom_id
      
        # initialize product defaults
        line_ids = []
        if sale_order_line_id:
            line_ids.append(sale_order_line_id)
        res = sale_order_line_obj.product_id_change_at(cr,mapped_uid,line_ids,
                                              pricelist=sale_order.pricelist_id.id,
                                              product=product_id,
                                              qty=product_qty,
                                              uom=product_uom_id,
                                              name=name,
                                              partner_id=partner.id,
                                              product_change=True)
        line_vals.update(res.get("value"))
        if notes:
            line_vals["notes"]=notes
        tax_id = line_vals.get("tax_id")
        if tax_id:
            line_vals["tax_id"]=[(6,0,tax_id)]
        # 
        # create
        if not sale_order_line_id:
            sale_order_line_id=sale_order_line_obj.create(cr,mapped_uid,
                                                          line_vals,context)        
        else: #update
            sale_order_line_obj.write(cr,mapped_uid,sale_order_line_id,
                                      line_vals,context)
            
        
        # create purchase order to sale order link
        link_obj._unlink_remote_ids(cr, mapped_uid, system.id, "purchase.order", remote_purchase_order_id)
        link_obj.create(cr, mapped_uid, {
                "system_id" : system.id,
                "name" : order_name,
                "local_model" : sale_order_obj._name,
                "local_id" : sale_order_id,
                "remote_model" : "purchase.order",
                "remote_id" : remote_purchase_order_id
            })
        
        # create purchase order line to sale order line link
        link_obj._unlink_remote_ids(cr, mapped_uid, system.id, "purchase.order.line", remote_purchase_line_id)
        link_obj.create(cr, mapped_uid, {
                "system_id" : system.id,
                "name" : name,
                "local_model" : sale_order_line_obj._name,
                "local_id" : sale_order_line_id,
                "remote_model" : "purchase.order.line",
                "remote_id" : remote_purchase_line_id
            })
        
        # create sale order to sale order link
        if remote_sale_order_id:
            link_obj._unlink_remote_ids(cr, mapped_uid, system.id, sale_order_obj._name, remote_sale_order_id)        
            link_obj.create(cr, mapped_uid, {
                "system_id" : system.id,
                "name" : sale_order_name,
                "local_model" : sale_order_obj._name,
                "local_id" : sale_order_id,
                "remote_model" : sale_order_obj._name,
                "remote_id" : remote_sale_order_id
            })
        return True
    
    
    def edi_fc_purchase_change_address(self, cr, uid, purchase, context=None):
        profile = self._profile_get(cr,uid)
        system = profile.system_id        
        mapped_uid = profile.property_mapped_user.id
        
        profile_obj = self.pool.get("edi.profile")
        sale_shop = self.pool.get("sale.shop")
        sale_order_obj = self.pool.get("sale.order")
        sale_order_line_obj = self.pool.get("sale.order.line")
        link_obj = self.pool.get("edi.link")
        address_obj = self.pool.get("res.partner.address")
        purchase_obj = self.pool.get("purchase.order")
        purchase_line_obj = self.pool.get("purchase.order.line")
        picking_obj = self.pool.get("stock.picking")
        
        name = purchase.get("name")       
        remote_sale_order_id = purchase.get("sale_order_id")
        remote_purchase_order_id = purchase.get("order_id")
        remote_purchase_line_id = purchase.get("id")
        address_id = profile_obj._edi_unpack_address(cr, mapped_uid, system, purchase.get("address"))
        supplier_ships = purchase.get("supplier_ships",False)
         
        if not remote_purchase_order_id:
            raise osv.except_osv(_("Error"), _("No Purchase Order ID transfered!"))
        if not remote_purchase_line_id:
            raise osv.except_osv(_("Error"), _("No Purchase Line ID transfered!"))
        if not address_id:
            raise osv.except_osv(_("Error"), _("No Address passed!"))
        if not name:
            raise osv.except_osv(_("Error"), _("No Name for Purchase Passed"))
        
        # check if sale order already exists
        sale_order_id = None
        # check sale order link
        if remote_sale_order_id:
            sale_order_id = link_obj._local_id(cr,mapped_uid,system.id,sale_order_obj._name,remote_sale_order_id)
            
        # check purchase order link
        if not sale_order_id:
            sale_order_id = link_obj._local_id(cr,mapped_uid,system.id,"purchase.order",remote_purchase_order_id,
                                               local_model=sale_order_obj._name)
        
        # check sale order line link
        sale_order_line_id = link_obj._local_id(cr,mapped_uid,system.id,"purchase.order.line",remote_purchase_line_id,
                                                local_model=sale_order_line_obj._name)
        if sale_order_line_id:
            sale_order_line = sale_order_line_obj.browse(cr,mapped_uid,sale_order_line_id)
            sale_order_id = sale_order_line.order_id.id
            

        #check sale order        
        if sale_order_id:        
            sale_order = sale_order_obj.browse(cr, mapped_uid, sale_order_id, context)
            shipping_address = sale_order.partner_shipping_id
            shop = sale_order.shop_id            
            #
            shop_id = self._edi_fc_determine_shop_id(cr, mapped_uid, profile, address_id, 
                                    direct_delivery=supplier_ships,context=context)   
            #
            new_shipping_address = address_obj.browse(cr, mapped_uid, address_id, context)            
            if new_shipping_address and shipping_address.id != new_shipping_address.id:                
                
                sale_order_obj.write(cr,mapped_uid,sale_order_id,{"partner_shipping_id" : address_id})
                sale_order_obj.log(cr, uid, sale_order_id, _("Corrected Shipping Address for Order %s from %s to %s")
                                    % (sale_order.name,shipping_address.name,new_shipping_address.name))
                
                #correct purchases
                
                purchase_line_ids = purchase_line_obj.search(cr,mapped_uid,[("sale_order_id","=",sale_order.id),
                                                                            ("dest_address_id","=",shipping_address.id)])
                for purchase_line in purchase_line_obj.browse(cr,mapped_uid,purchase_line_ids,context):
                    purchase_obj.write(cr,mapped_uid, [purchase_line.order_id.id], {"dest_address_id" : new_shipping_address.id }, context)
                    purchase_line_obj.write(cr,mapped_uid,[purchase_line.id], {"dest_address_id" : new_shipping_address.id }, context)
                    
                #correct pickings
                
                picking_ids = picking_obj.search(cr,mapped_uid,[("sale_id","=",sale_order_id),("address_id","=",shipping_address.id)],context)
                picking_obj.write(cr,mapped_uid,picking_ids,{"address_id" : new_shipping_address.id },context)
                
            if shop_id and shop.id != shop_id:
                new_shop = sale_shop.browse(cr,mapped_uid,shop_id,context)
                sale_order_obj.log(cr, uid, sale_order_id, _("Corrected Shop for Order %s from %s to %s")
                                    % (sale_order.name,shop.name,new_shop.name))
                
                sale_order_obj.write(cr,mapped_uid,sale_order_id,{"shop_id" : new_shop.id})
                purchase_line_ids = purchase_line_obj.search(cr,mapped_uid,[("sale_order_id","=",sale_order.id),("shop_id","=",shop.id)],context)
                purchase_line_obj.write(cr,mapped_uid,purchase_line_ids,{"shop_id" : new_shop.id },context)
              
                 
        return True
    

    _inherit = "edi.server_profile"
    _columns = {
        "shop_id" : fields.many2one("sale.shop", "Shop"),
        "dd_shop_id" : fields.many2one("sale.shop", "Direct Delivery Shop"),
        "country_shop_ids" : fields.one2many("edi.country.shop","server_profile_id","Country to Shop Mappings")       
    }
server_profile()

class edi_country_shop(osv.osv):
    _name = "edi.country.shop"    
    _description = "EDI Country to Shop Mapping"
    _columns = {                
        "server_profile_id" : fields.many2one("edi.server_profile","Server Profile",required=True,select=True),
        "country_id" : fields.many2one("res.country","Country",required=True,select=True),
        "shop_id" : fields.many2one("sale.shop", "Shop"),
        "dd_shop_id" : fields.many2one("sale.shop", "Direct Delivery Shop")
    }
edi_country_shop()

class purchase_order(osv.osv):
    
    def edi_tv_purchase(self, cr, uid, ids, context=None):
        transfer_obj = self.pool.get("edi.transfer")
        order_line_obj= self.pool.get("purchase.order.line")
        for purchase in self.browse(cr, uid, ids, context):
            for line in purchase.order_line:
                #execute as admin
                transfer_obj._call(cr,1,
                                  purchase.partner_id.id,
                                  order_line_obj._name,
                                  line.id,
                                  order_line_obj.edi_tv_purchase)
        return True
            
    def edi_tv_change_address(self, cr, uid, ids, context=None):
        transfer_obj = self.pool.get("edi.transfer")
        order_line_obj= self.pool.get("purchase.order.line")
        for purchase in self.browse(cr, uid, ids, context):
            for line in purchase.order_line:
                #execute as admin
                transfer_obj._call(cr,1,
                                  purchase.partner_id.id,
                                  order_line_obj._name,
                                  line.id,
                                  order_line_obj.edi_tv_change_address)
        return True
            
    _inherit = "purchase.order"
purchase_order()


class purchase_order_line(osv.osv):
    
    def _edi_pack_purchase_order_line(self, cr, uid, oid, profile, context=None):
        line = self.browse(cr, uid, oid, context)
        profile_obj = self.pool.get("edi.profile")
        
        sale_order = line.sale_order_id
        sale_order_line = line.sale_order_line_id
        purchase_order = line.order_id
                   
        system = profile.system_id                        
        data = {
            "id" : line.id,
            "order_id" : line.order_id.id,
            "order_name" : purchase_order.name,
            "sale_order_id" : sale_order and sale_order.id or None,
            "sale_order_line_id" : sale_order_line and sale_order_line.id or None,
            "sale_order_name" : sale_order and sale_order.name or None,
            "supplier_ships" : purchase_order.supplier_ships,
            "name" : line.name,
            "date_planned" : line.date_planned,
            "data_order" : line.date_order,
            "notes" : line.notes,
            "product_uom" : profile_obj._edi_pack_uom(cr,uid,system,line.product_uom),
            "product" : profile_obj._edi_pack_product(cr,uid,system,line.product_id),
            "product_qty" : line.product_qty
        }
        
        if purchase_order.dest_address_id:
            data["address"] = profile_obj._edi_pack_address(cr,uid,system,purchase_order.dest_address_id)
        return data
    
    def edi_tv_purchase(self, cr, uid, oid, profile, proxy, context=None):   
        line = self.browse(cr, uid, oid, context)
        if line.state!="draft":
            return True 
        data = self._edi_pack_purchase_order_line(cr, uid, oid, profile, context)        
        proxy.get("edi.server_profile").edi_fc_purchase(cr,uid,data,context)
        return True
    
    def edi_tv_change_address(self, cr, uid, oid, profile, proxy, context=None):   
        data = self._edi_pack_purchase_order_line(cr, uid, oid, profile, context)        
        proxy.get("edi.server_profile").edi_fc_purchase_change_address(cr,uid,data,context)
        return True
    
    _inherit = "purchase.order.line"
purchase_order_line()