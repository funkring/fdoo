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
from base.res import res_log
from at_base import task
from openerp.tools.translate import _

class ProductImportAdapter(task.ImportAdapter):
   
    def __init__(self, pool, cr, uid, import_task, validation=False, context=None):
        super(ProductImportAdapter,self).__init__(pool, cr, uid, "product.import_task", import_task, validation, context)              
        
        self.product_obj = pool.get("product.product")
        self.pricelist_item_obj = pool.get("product.pricelist.item")
        self.sale_pricelist = import_task.sale_pricelist_id and import_task.sale_pricelist_id.active_version_id or None 
        self.sale_pricelist2 = import_task.sale_pricelist_2_id and import_task.sale_pricelist_2_id.active_version_id  or None
                                                                
        product_fields = self.product_obj.fields_get_keys(cr,uid,context)
        self.product_defaults = self.product_obj.default_get(cr,uid,product_fields,context)                                
        self.receipt_account_id = None
        self.parent_account_id = None        
        self.default_taxes_ids = [1]        
        
        #fields filter
        self.update_only = import_task.update_only
        update_only_fields = import_task.update_only_fields       
        if update_only_fields:
            self.update_fields_filter = update_only_fields.split(",")
        else:
            self.update_fields_filter = None
        
        #get accounts
        account_obj = self.pool.get("account.account")        
        ids = account_obj.search(cr,uid,[("code","=","4000")])
        if ids:
            self.receipt_account_id = ids[0]
        else:
            self.log("Receipt Account 4000 not found", res_log.SEVERITY_BLOCKER)
        
        
        ids = account_obj.search(cr,uid,[("code","=","V4000")])
        if ids:
            self.parent_account_id = ids[0]
        else:
            self.log("Receipt parent Account V4000 not found",res_log.SEVERITY_BLOCKER)
        
        if validation:
            self.log("Validation started!", res_log.SEVERITY_NORMAL)
        else:
            self.log("Import started!", res_log.SEVERITY_NORMAL)
                         
    def getProductId(self,value):        
        return self.getObjectId("Product", "product.product", value,"default_code")        
                          
    def getAccountId(self,value):        
        return self.getObjectId("Account", "account.account", value,"code")
        
    def getCategoryId(self,value,warning=False):
        return self.getObjectId("Category", "product.category", value,"code",warning=warning)   
                  
    def getUomId(self,value,warning=False):
        return self.getObjectId("UOM", "product.uom", value,"code",field2="name",warning=warning)
       
    def getPartnerId(self,value,field="name"):
        return self.getObjectId("Partner","res.partner", value, "name")        
    
    def validateRow(self):
        self.product_name = self.productName()
        self.product_ref = self.productCode()
        
        if not self.product_ref or not self.product_name:
            self.log(_("No product reference or name found on line %d") % (self.row(),), res_log.SEVERITY_WARNING)
            return False
                        
        self.product_id = self.getProductId(self.product_ref)        
        self.uom_id = self.getUomId(self.productUom())
        self.supplier_delivery_days = self.productSupplierDeliverDays()        
        
        #values        
        if not self.uom_id:
            self.uom_id = self.product_defaults.get("uom_id",None)
                        
        self.product_variants=self.productVariant()
        self.product_shortcut=self.productShortcut()
        self.category_id=self.getCategoryId(self.productCategoryCode())
        self.supplier_taxes_id=[(6,0,self.default_taxes_ids)]
        self.taxes_id=[(6,0,self.default_taxes_ids)]
        self.product_type=(self.is_service() and "service") or "consu"
        self.supply_method="buy"
        self.standard_price=self.productCostPrice()
        self.price_extra=0.0
        self.list_price=self.productPrice()
        self.sale_delay=self.supplier_delivery_days or 3
        self.produce_delay=self.supplier_delivery_days or 3
        self.procure_method="make_to_order"
        self.sale_ok=True
        self.purchase_ok=not self.is_service()
        self.weight_net=self.productWeightNetto()
        self.weight=self.productWeightBrutto()
        self.margin2=self.productDistributorMargin()
        return True
        
                                        
    def importRow(self):
        if self.validateRow():
            values = None
            if not self.product_id:
                values = self.product_defaults.copy()
            else:
                values = {}    
            values["default_code"]=self.product_ref
            values["name"]=self.product_name
            values["variants"]=self.product_variants
            values["shortcut"]=self.product_shortcut
            values["categ_id"]=self.category_id
            values["uom_id"]=self.uom_id
            values["uom_po_id"]=self.uom_id
            values["supplier_taxes_id"]=self.supplier_taxes_id
            values["taxes_id"]=self.taxes_id                   
            values["type"]=self.product_type
            values["supply_method"]=self.supply_method
            values["standard_price"]=self.standard_price
            values["price_extra"]=self.price_extra
            values["list_price"]=self.list_price
            values["sale_delay"]=self.sale_delay
            values["produce_delay"]=self.produce_delay
            values["procure_method"]=self.procure_method
            values["sale_ok"]=self.sale_ok
            values["purchase_ok"]=self.purchase_ok        
            values["weight_net"]=self.weight_net  
            values["weight"]=self.weight
          
            #supplier
            supplier_sequence = 1
            for supplier_name in self.productSupplierNames():            
                partner_id = self.getPartnerId(supplier_name)
                if partner_id:
                    supplier_values = {
                        "name" : partner_id,
                        "product_uom" : self.uom_id,
                        "delay" : self.supplier_delivery_days,
                        "min_qty" : 0.0,
                        "sequence" : supplier_sequence
                    }                 
                    supplier_sequence+=1       
                    ids = None
                    if self.product_id:
                        ids = self.pool.get("product.supplierinfo").search(self.cr,self.uid,[("name","=",partner_id),("product_id","=",self.product_id)])
                    seller_ids = values.get("seller_ids")
                    if not seller_ids:
                        seller_ids=[]
                        values["seller_ids"]=seller_ids
                    
                    if ids:
                        seller_ids.append((1,ids[0],supplier_values))
                    else:
                        seller_ids.append((0,0,supplier_values))
               
            self.updateProductValues(values)                  
            if self.product_id:                
                if self.update_fields_filter:
                    allowed_values = {}
                    for tField in self.update_fields_filter:
                        allowed_values[tField]=values.get(tField)
                    values = allowed_values                
                if values:
                    self.product_obj.write(self.cr,self.uid,self.product_id,values,context=self.context)
            elif not self.update_only:
                self.product_id = self.product_obj.create(self.cr,self.uid,values,context=self.context)
                
            #pricelist for distributor            
            if self.product_id and not self.update_fields_filter and self.sale_pricelist2 and self.margin2:
                ids = self.pricelist_item_obj.search(self.cr,self.uid,[("price_version_id","=",self.sale_pricelist2.id),("product_id","=",self.product_id),("sequence","=",1)])
                pricelist_item = {
                    "name" : self.product_ref,
                    "price_version_id" : self.sale_pricelist2.id,
                    "product_id" : self.product_id,                    
                    "min_quantity" : 0,
                    "base" : 2,
                    "price_discount" : self.margin2 / 100.0,
                    "sequence" : 1
                }                
                if not ids:
                    self.pricelist_item_obj.create(self.cr,self.uid,pricelist_item,context=self.context)
                else:
                    self.pricelist_item_obj.write(self.cr,self.uid,ids,pricelist_item,context=self.context)         
                    
            return True
        return False
    
    def _init_next_row(self):   
        pass
      
    def rowCount(self):
        return 0 
       
    def row(self):
        return 0
       
    def close(self):
        pass
    
    def hasNext(self):
        return False
    
    def rewind(self):
        pass
    
    def productValidate(self):
        pass
        
    def is_service(self):
        return False
                          
    def productCode(self):
        return None
    
    def productParentCode(self):
        return None
    
    def productName(self):
        return None
    
    def productVariant(self):
        return None
    
    def productCategoryCode(self):
        return None
    
    def productUom(self):
        return None
            
    def productSupplierName(self):
        return None
    
    def productSupplierDeliverDays(self):
        return None

    def productIncomeAccount(self):
        return None
    
    def productIncomeAccountName(self):
        return None
    
    def productExpenseAccount(self):
        return None
    
    def productExpenseAccountName(self):
        return None
    
    def productShortcut(self):
        return None
    
    def productCostPrice(self):
        return None
    
    def productPrice(self):
        return None
    
    def productMargin(self):
        return None
    
    def productPriceDistributor(self):
        return None
    
    def productDistributorMargin(self):
        return None

    def productWeightNetto(self):
        return None
    
    def productWeightBrutto(self):
        return None

class product_import_task(osv.osv):
    _inherit = "task.import_template"
    _name = "product.import_task"
    _description = "Product Import"
    _columns = {        
        "sale_pricelist_id" : fields.many2one("product.pricelist","Sales Pricelist",required=True,readonly=True, states={'new': [('readonly', False)]}),
        "sale_pricelist_2_id" : fields.many2one("product.pricelist","Resale Pricelist",required=True,readonly=True, states={'new': [('readonly', False)]}),
        "update_only_fields" : fields.char("Update only Fields",size=128,readonly=True, states={'new': [('readonly', False)]}),
        "update_only" : fields.boolean("Update Only",readonly=True, states={'new': [('readonly', False)]}),
        "log_ids" : fields.one2many("res.log","res_id","Logs",domain=[("res_model","=","product.import_task")],readonly=True)
    }
product_import_task()   
