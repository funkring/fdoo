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
from at_base import extfields
from openerp.tools.translate import _


class edi_profile(osv.osv):
    
    def _edi_pack_uom(self,cr,uid,system,uom,context=None):
        res = []
        if uom:
            if uom.name:
                res.append(uom.name)
            if uom.code:
                res.append(uom.code)
        return res
    
    def _edi_pack_taxes(self,cr,uid,system,taxes,context=None):
        res = []
        if taxes:
            for tax in taxes:
                tax_res = []
                if tax.description:
                    tax_res.append(tax.description)
                if tax.name:
                    tax_res.append(tax.name)
                if tax_res:
                    res.append(tax_res)
        return res  
    
    def _edi_unpack_uom(self,cr,uid,system,data,context=None):
        if data:
            uom_obj = self.pool.get("product.uom")
            for value in data:
                uom_ids = uom_obj.search(cr,uid,[("code","=",value)]) or None
                if not uom_ids:                   
                    uom_ids = uom_obj.search(cr,uid,[("name","=",value)]) or None                    
                return uom_ids and uom_ids[0] or None
        return None
    
    def _edi_unpack_taxes(self,cr,uid,system,data,context=None):
        res = []
        if data:
            tax_obj = self.pool.get("account.tax")
            for tax in data:
                for tax_val in tax:
                    tax_ids = tax_obj.search(cr,uid,[("description","=",tax_val)])
                    if not tax_ids:
                        tax_ids=tax_obj.search(cr,uid,[("name",tax_val)])
                    if tax_ids:
                        res.append(tax_ids[0])
        return res

    
    def _edi_pack_product(self,cr,uid,system,product,context=None):
        local_context = {
           "partner_id" : system.partner_id
        }
        
        link_obj = self.pool.get("edi.link")
        product_obj = self.pool.get("product.product")
        partner_product = product_obj.browse(cr,uid,product.id,local_context)
                
        res = {
            "id" : partner_product.id,
            "link_id" : link_obj._remote_id(cr,uid,system.id,"product.product",partner_product.id),
            "name" : partner_product.partner_ref,            
            "code" : partner_product.code            
        }
        return res
    
    def _edi_unpack_product(self,cr,uid,system,data,context=None):
        if not data:
            return None                
        link_obj = self.pool.get("edi.link")                
        product_id = link_obj._local_id(cr,uid,system.id,"product.product",data.get("link_id"))
        if not product_id:
            product_obj = self.pool.get("product.product")
            product_code = data.get("code")
            product_name = data.get("name")
            if product_code:                            
                product_ids = product_obj.search(cr,uid,[("default_code","=",product_code)])
                product_id = product_ids and product_ids[0] or None
            if not product_id and product_name:
                product_ids = product_obj.search(cr,uid,[("name","=",product_name)])
                product_id = product_ids and product_ids[0] or None          
            if not product_id and product_code:
                product_ids = product_obj.search(cr,uid,[("default_code","like",product_code)])
                product_id = product_ids and product_ids[0] or None
        return product_id
            
            
    _inherit = "edi.profile"
edi_profile()    


class server_profile(osv.osv):
    
    def edi_fc_products(self, cr, uid, context=None):        
        profile = self._profile_get(cr,uid)
        system = profile.system_id
        partner = system.partner_id
        mapped_uid = profile.property_mapped_user.id
        
        product_obj = self.pool.get("product.product")
        pricelist_obj = self.pool.get("product.pricelist")
        profile_obj = self.pool.get("edi.profile")
        
        res = []
        category_ids = [c.id for c in profile.product_category_ids]
        for product in product_obj.browse(cr,mapped_uid,
                                          product_obj.search(cr,mapped_uid,[("categ_id","in",category_ids),
                                                                            ("sale_ok","=",True),
                                                                            '|',("state","=",False),
                                                                                ("state","=","sellable")]),
                                          context):
            
            price = product.list_price
            uom = (product.uos_id and product.uos_id) or (product.uom_id and product.uom_id)
            pricelist = partner.property_product_pricelist
            if pricelist:
                price = pricelist_obj.price_get(cr,mapped_uid,[pricelist.id],
                                        product.id, 1.0, partner.id, {
                                          "uom" : uom.id
                                        })[pricelist.id]
                        
            #
            val = {
                "id" : product.id,
                "name" : product.name,
                "variants" : product.variants,
                "categ_id" : product.categ_id.id,
                "type" : product.type,
                "supply_method" : product.supply_method,
                "description" : product.description_sale,
                "sale_delay" : product.sale_delay,
                "produce_delay" : product.produce_delay,
                "procure_method" : product.procure_method,
                "volume" : product.volume,
                "weight" : product.weight,
                "weight_net" : product.weight_net,
                "cost_method" : product.cost_method,
                "warranty" : product.warranty,
                "uom" : profile_obj._edi_pack_uom(cr,uid,system,uom),                
                "mes_type" : product.mes_type,
                "list_price" : price,
                "code" : product.code,
                "qty_available" : product.qty_available,
                
            }
            #
            taxes = profile_obj._edi_pack_taxes(cr,uid,system,product.taxes_id)
            if taxes:
                val["tax"]=taxes            
            res.append(val)
            #            
        return res
        
    _inherit = "edi.server_profile"
    _columns = {
        "product_category_ids" : fields.many2many("product.category",
                                                  "edi_server_profile_product_category_rel","system_id","category_id",
                                                  string="Product Categories")
    }     
server_profile()


class client_profile(osv.osv):
  
    def _edi_tv_do_sync(self,cr,uid,ids,func,context=None):
        added = 0
        deleted = 0
        updated = 0
        errors={}
        for profile in self.browse(cr, uid, ids, context):
            proxy = self._proxy_get(cr,uid,profile,context)        
            if proxy:
                res = func(cr,uid,profile,proxy,errors,context)       
                added+=res["added"]
                deleted+=res["deleted"]
                updated+=res["updated"]       
        
        info_obj = self.pool.get("at_base.info_wizard")
        
            
        message =  _("= Statistic =\n"
                     "\n"                     
                     "Added: %s\n"
                     "Updated: %s\n"
                     "Deleted: %s\n"
                     "\n"
                     "\n"
                     "= Warnings = \n"
                     "\n"
                     "%s") % (added,updated,deleted,"\n".join(errors.values()))        
        return info_obj.do_show(cr,uid,None,None,message,context)

    def _edi_tv_product_sync(self,cr,uid,profile,proxy,errors,context=None):        
        link_obj = self.pool.get("edi.link")
        server_obj = proxy.get("edi.server_profile")
        product_obj = self.pool.get("product.product")
        supplier_obj = self.pool.get("product.supplierinfo")
        profile_obj = self.pool.get("edi.profile")
        system = profile.system_id
        added = 0
        updated = 0
        #        
        remote_products = server_obj.products(cr,uid)
        for remote_product in remote_products:
            remote_product_id = remote_product.get("id")
            remote_product_code = remote_product.get("code")
            #
            product_id = link_obj._local_id(cr,uid,system.id,"product.product",remote_product_id)            
            nolink = not product_id
            #
            if not product_id and profile.product_has_same_ref and remote_product_code:
                product_ids = product_obj.search(cr,uid,[("default_code","=",remote_product_code)])
                product_id = product_ids and product_ids[0] or None
            #
            product_variants = remote_product.get("variants")
            product_name = remote_product.get("name")
            product_full_name = product_variants and ("%s - %s" % (product_name, product_variants)) or product_name
             
            seller_vals = {                    
                "product_name" : product_full_name,
                "product_code" : remote_product.get("code"),
                "delay" : remote_product.get("sale_delay")
            }
            
            if not product_id:
                seller_vals["name"] = system.partner_id.id
                seller_vals["min_qty"] = 1.0
                                    
                vals = {
                    "name" : remote_product.get("name"),
                    "variants" : remote_product.get("variants"),
                    "type" : remote_product.get("type"),
                    "supply_method" : remote_product.get("supply_method"),
                    "description_purchase" : remote_product.get("description"),
                    "sale_delay" : remote_product.get("sale_delay"),
                    "produce_delay" : remote_product.get("produce_delay"),
                    "procure_method" : remote_product.get("procure_method"),                        
                    "list_price" : remote_product.get("list_price"),
                    "weight" : remote_product.get("weight"),
                    "weight_net" : remote_product.get("weight_net"),
                    "cost_method" : remote_product.get("cost_method"),
                    "warranty" : remote_product.get("warranty"),
                    "mes_type" : remote_product.get("mes_type"),                        
                    "sale_ok" : True,
                    "purchase_ok" : True,
                    "seller_ids" : [(0,0,seller_vals)]
                }
                
                if profile.product_has_same_ref:
                    vals["default_code"]=remote_product.get("code")
                
                uom_value = remote_product.get("uom")
                uom_id = profile_obj._edi_unpack_uom(cr,uid,system,uom_value)
                #
                if not uom_id:
                    if uom_value:
                        errors[str(uom_value)]=_("Unit '%s' not found") % (uom_value,)
                    else:
                        errors[product_full_name]=_("No Unit for Product '%s' found") % (product_full_name,)
                #                                           
                # create product
                product_id=product_obj.create(cr,uid,vals,context)                   
                added+=1
            else:
                product = product_obj.browse(cr, uid, product_id, context)              
                product_template_id = product.product_tmpl_id.id 
                supplier_ids = supplier_obj.search(cr,uid,[("product_id","=",product_template_id),
                                                           ("name","=",system.partner_id.id)])
                if not supplier_ids:
                    seller_vals["name"] = system.partner_id.id
                    seller_vals["min_qty"] = 1.0
                    seller_vals["product_id"]=product_template_id
                    supplier_obj.create(cr,uid,seller_vals,context)
                else:
                    supplier_obj.write(cr,uid,supplier_ids,seller_vals,context)
                #
                updated+=1
            #
            # check for creating link
            if product_id and nolink:
                #create reference
                link_obj.create(cr,uid,{
                    "name" : product_full_name,
                    "system_id" : system.id,                    
                    "local_model" : "product.product",
                    "local_id" : product_id,                    
                    "remote_model" : "product.product",
                    "remote_id" : remote_product_id
                },context)                    
        #
        return { "added" : added, "deleted" : 0, "updated" : updated }
    
    def do_product_sync(self, cr, uid, ids, context=None):
        return self._edi_tv_do_sync(cr, uid, ids, self._edi_tv_product_sync, context)
   
    _inherit = "edi.client_profile"        
    _columns = {
        "product_category_ids" : extfields.one2many_rel("system_id","edi.product_category","system_id",
                                                        string="Product Categories"),
        "product_sync" : fields.selection([("download","Download"),("upload","Upload"),("both","Both")],"Sync Direction",required=True),
        "product_has_same_ref" : fields.boolean("Same Reference"),
    }    
    _defaults = {
        "product_sync" : "download"        
    }
client_profile()
    