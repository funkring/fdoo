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
from base.res import res_log
from at_base import task
import re

class PartnerImportAdapter(task.ImportAdapter):
    
    def __init__(self, pool, cr, uid, import_task, validation=False, context=None):         
        super(PartnerImportAdapter,self).__init__(pool, cr, uid, "partner.import_task", import_task, validation, context)
        self.partner_obj = pool.get("res.partner")
        self.partner_address_obj = pool.get("res.partner.address")
        self.account_obj = self.pool.get("account.account")         
        self.mobile_pattern = re.compile('[+43()0 ]+66.*', re.I)
        self.supplier_flag = import_task.type == "supplier"
        self.customer_flag = import_task.type == "customer"
        self.prospective_flag = import_task.type == "prospective"
        self.mixed_flag = import_task.type == "mixed"
        
        #get defaults
        fields = self.partner_obj.fields_get_keys(cr,uid,context)
        self.defaults = self.partner_obj.default_get(cr,uid,fields,context)
      
        #get accounts       
        ids = self.account_obj.search(cr,uid,[("code","=","KUNDEN")])
        if ids:
            self.debitor_parent_account_id = ids[0]
        else:
            self.log("Debitor parent account KUNDEN not found", res_log.SEVERITY_BLOCKER)
        
        #get accounts       
        ids = self.account_obj.search(cr,uid,[("code","=","LIEFERANTEN")])
        if ids:
            self.creditor_parent_account_id = ids[0]
        else:
            self.log("Creditor parent account LIEFERANTEN not found", res_log.SEVERITY_BLOCKER)
      
        #get accounts       
        ids = self.account_obj.search(cr,uid,[("code","=","2000")])
        if ids:
            self.debitor_default_account_id = ids[0]
        else:
            self.log("Debitor parent account 2000 not found", res_log.SEVERITY_BLOCKER)
        
        #get accounts       
        ids = self.account_obj.search(cr,uid,[("code","=","3000")])
        if ids:
            self.creditor_default_account_id = ids[0]
        else:
            self.log("Creditor parent account 3000 not found", res_log.SEVERITY_BLOCKER)
            
        #accounts
        self.debitor_account_ids = []
        self.creditor_account_ids = []
        
 
    def is_mobil(self,num):
        if num:
            self.mobile_pattern.match(num)            
        return False
     
    def getAccountId(self,value,field="code",partner_name=None,debitor=False,creditor=False):        
        res = None
        if value:
            attribCache = self.getAttribCache("account.account") 
            res = attribCache.get(value)
            if not res and not attribCache.has_key(value):
                ids = self.pool.get("account.account").search(self.cr,self.uid,[(field,"=",value)])
                if ids:
                    res = ids[0]                
                if not res:                    
                    if creditor and partner_name:
                        if not self.validation:
                            res = self.account_obj.copy(self.cr,self.uid,self.creditor_default_account_id, 
                                {"code":value,
                                 "name" : partner_name }, context=self.context)
                            self.log("Creditor Account %s for partner %s created" % (value,partner_name),res_log.SEVERITY_WARNING)
                            self.creditor_account_ids.append(res)
                        else:
                            self.log("Creditor Account %s for partner %s will be created" % (value,partner_name),res_log.SEVERITY_WARNING)
                    elif debitor and partner_name:
                        if not self.validation:                                
                            res = self.account_obj.copy(self.cr,self.uid,self.debitor_default_account_id, 
                                {"code":value,
                                 "name" : partner_name }, context=self.context)
                            self.debitor_account_ids.append(res)
                            self.log("Debitor Account %s for partner %s created" % (value,partner_name),res_log.SEVERITY_WARNING)                            
                        else:
                            self.log("Debitor Account %s for partner %s will be created" % (value,partner_name),res_log.SEVERITY_WARNING)
                    else:
                        self.log("Account with %s %s not found" % (field,value),res_log.SEVERITY_BLOCKER)                    
                attribCache[value]=res
        return res
    
    def getTitleId(self,value,domain=None):        
        return self.getObjectId("Title", "res.partner.title", value, "name",domain=domain)        
    
    def getPartnerId(self,value,warning=True,error=True):
        return self.getObjectId("Partner", "res.partner", value, "ref",warning=warning,error=error)
    
    def getCountryId(self,value):
        if value:            
            if value == "A":
                value="AT"
            elif value == "D":
                value="DE"
            elif value == "H":
                value="HU"
                    
        return self.getObjectId("Country", "res.country", value, "code")
    
    
    def getAddressId(self,partner_id):
        if partner_id:
            ids = self.partner_address_obj.search(self.cr,self.uid,[("partner_id","=",partner_id),("type","=","default")])
            return (ids and ids[0]) or None
        return None 


    def validateRow(self):        
        self.partner_ref = self.partnerCode()
        self.partner_name = self.partnerName()
        if self.partner_ref and self.partner_name:
            
            #partner accounts
            partner_debitor_account = self.partnerDebitorAccount()
            partner_creditor_account = self.partnerCreditorAccount()
            
            #get partner id
            self.partner_id = self.getPartnerId(self.partner_ref)
            if not self.partner_id and partner_debitor_account:
                self.partner_id = self.getPartnerId(partner_debitor_account,warning=False,error=False)
            if not self.partner_id and partner_creditor_account:
                self.partner_id = self.getPartnerId(partner_creditor_account,warning=False,error=False)
        
            #accounts     
            self.debitor_account_id = self.getAccountId(partner_debitor_account,partner_name=self.partner_name, debitor=True)
            self.creditor_account_id = self.getAccountId(partner_creditor_account, partner_name=self.partner_name, creditor=True)
            
            #vat 
            self.vat = self.partnerUID()
            self.supplier = self.is_supplier()
            self.customer = self.is_customer()
            
            #address
            self.partner_contact = self.partnerContact()
            self.partner_contact_title_id = self.getTitleId(self.partnerContactTitle(),domain=("domain","=","contact"))
            self.address_id = self.getAddressId(self.partner_id)
            self.partner_title_id = self.getTitleId(self.partnerTitle(),domain=("domain","=","partner"))
            self.land_id = self.getCountryId(self.partnerCountryCode())
            self.street = self.partnerStreet()
            self.street2 = self.partnerStreet2()
            self.city = self.partnerCity()
            self.zip = self.partnerZip()
            self.phone = self.partnerPhone()
            self.mobilePhone = self.partnerMobilePhone()
            self.fax = self.partnerFax()
            self.email = self.partnerEMail()
            self.function = self.partnerFunction()           
            return True
        return False
        
    
    def importRow(self):
        if self.validateRow():
            values = None
            if not self.partner_id:
                values = self.defaults.copy()
            else:
                values = {}
            
            if "AIDA" in self.partner_name:
                pass 
            
            values["name"]=self.partner_name
            values["ref"]= self.partner_ref
            
            if self.partner_title_id:
                values["title"]=self.partner_title_id
            else:
                values["title"]=None
                            
            if self.vat:
                values["vat"]=self.vat
            
            if self.customer:                
                values["customer"]=True
                
            if self.supplier:
                values["supplier"]=True
                
            if self.creditor_account_id:
                values["property_account_payable"]=self.creditor_account_id
                
            if self.debitor_account_id:
                values["property_account_receivable"]=self.debitor_account_id
         
            address = {}
            if self.partner_contact_title_id:
                address["title"]=self.partner_contact_title_id
            if self.land_id:
                address["country_id"]=self.land_id
            if self.street:
                address["street"]=self.street
            
            if self.street2:
                address["street2"]=self.street2
          
            if self.city:
                address["city"]=self.city
            if self.zip:
                address["zip"]=self.zip
            if self.phone:
                address["phone"]=self.phone
            if self.fax:
                address["fax"]=self.fax
            if self.mobilePhone:
                address["mobile"]=self.mobilePhone
            if self.function:
                address["function"]=self.function
                
            if address:
                if not address.has_key("street2"):
                    address["street2"]=None
                if not address.has_key("street"):
                    address["street"]=None
                if not address.has_key("title"):
                    address["title"]=None
                    
                address["type"]="default"
                address["name"]=self.partner_contact                                
                if self.address_id:
                    self.partner_address_obj.write(self.cr,self.uid,self.address_id,address,context=self.context)                    
                else:                     
                    values["address"]= [(0,0,address)]
                  
              
            if self.partner_id:
                self.partner_obj.write(self.cr,self.uid,self.partner_id,values,self.context)
            else:
                self.partner_obj.create(self.cr,self.uid,values,self.context)                
            return True        
        return False
  
    def _init_next_row(self):   
        pass
      
    def is_customer(self):
        return self.customer_flag
    
    def is_supplier(self):
        return self.supplier_flag
    
    def is_prospective(self):
        return self.prospective_flag
          
    def rowCount(self):
        return 0 
       
    def row(self):
        return 0
       
    def close(self):        
        if self.debitor_account_ids:
            self.pool.get("account.account").write(self.cr,self.uid,self.debitor_account_ids,{"parent_id" : self.debitor_parent_account_id },context=self.context)
        
        if self.creditor_account_ids:
            self.pool.get("account.account").write(self.cr,self.uid,self.debitor_account_ids,{"parent_id" : self.creditor_parent_account_id },context=self.context)
        
    
    def hasNext(self):
        return False
    
    def rewind(self):
        pass
    
    def partnerCode(self):
        return None
   
    def partnerName(self):
        return None
    
    def partnerStreet(self):
        return None
    
    def partnerStreet2(self):
        return None
    
    def partnerTitle(self):
        return None
    
    def partnerContact(self):
        return None
        
    def partnerContactTitle(self):
        return None
        
    def partnerCountryCode(self):
        return None
    
    def partnerZip(self):
        return None
    
    def partnerCity(self):
        return None
    
    def partnerPhone(self):
        return None
    
    def partnerMobilePhone(self):
        return None
    
    def partnerFax(self):
        return None
    
    def partnerEMail(self):
        return None
    
    def partnerUID(self):
        return None
    
    def partnerDebitorAccount(self):
        return None
    
    def partnerCreditorAccount(self):
        return None
    
    def partnerNote(self):
        return None
    
    def partnerFunction(self):
        return None
   

class partner_import_task(osv.osv):
    _inherit = "task.import_template"
    _name = "partner.import_task"
    _description = "Partner Import"    
    _columns = {
        "type" : fields.selection([("supplier","Supplier"),
                                   ("customer","Customer"),
                                   ("prospective","Prospective Customer"),
                                   ("mixed","Mixed")],"Type",required=True,readonly=True,states={'new': [('readonly', False)]}),
        "log_ids" : fields.one2many("res.log","res_id","Logs",domain=[("res_model","=","partner.import_task")],readonly=True)
    }
partner_import_task()      
    