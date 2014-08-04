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
from at_base import util
from at_base.proxy import RPCProxy

from openerp.tools.translate import _

import netsvc
import traceback

class edi_system(osv.osv):
    
    _name = "edi.system"
    _description= "EDI System"    
    _columns = {
        "name" : fields.char("Name",size=32,required=True,select=True),
        "partner_id" : fields.many2one("res.partner","Partner",required=True,select=True),        
        "links" : fields.one2many("edi.link","system_id","Links"),
        "client_profile_ids" : fields.one2many("edi.client_profile","system_id","Client Profile",domain=[("enabled","=",True)]),
        "server_profile_ids" : fields.one2many("edi.server_profile","system_id","Server Profile",domain=[("enabled","=",True)])
    }        
edi_system()    
    
    
class edi_profile(osv.osv):
    
    def _edi_pack_title(self, cr, uid, system, title):
        res = []
        if title.shortcut:
            res.append(title.shortcut)
        if title.name:
            res.append(title.name)       
        return res 
            
    def _edi_unpack_title(self, cr, uid, system, data):
        if data:
            title_obj = self.pool.get("res.partner.title")
            for value in data:
                title_ids = title_obj.search(cr,uid,[("shortcut","=",value),("domain","=","contact")])
                if not title_ids:
                    title_ids = title_obj.search(cr,uid,[("name","=",value),("domain","=","contact")])
                if title_ids:
                    return title_ids[0] or None            
        return None
        
    def _edi_pack_address(self, cr, uid, system, address):
        res = None
        if address:
            res = { "id" : address.id,
                    "is_standalone" : True
                   }
            partner = address.partner_id
            company_obj = self.pool.get("res.company")
            #
            if partner and company_obj.search(cr, uid, [("partner_id","=",partner.id)],count=True) > 0:
                res["is_standalone"]=False
            #
            if partner:
                res["partner_title"]=self._edi_pack_title(cr,uid,system,partner.title)
                res["partner_name"]=partner.name  
            #
            if address.title:
                res["title"]=self._edi_pack_title(cr,uid,system,address.title)
            #    
            res["name"]=address.name
            res["street"]=address.street
            res["street2"]=address.street2
            res["zip"]=address.zip
            res["city"]=address.city
            if address.country_id:
                res["country"]=address.country_id.code
        return res
    
    def _edi_unpack_address(self, cr, uid, system, data, address_type="delivery", modify=True):
        address_id = None
        if data:
            remote_id = data.get("id")
            #
            partner = system.partner_id
            title_id = self._edi_unpack_title(cr, uid, system,data.get("title"))
            partner_name = data.get("partner_name")
            name = data.get("name")
            street = data.get("street")
            street2 = data.get("street2")
            city_zip = data.get("zip")
            city = data.get("city")
            is_standalone = data.get("is_standalone")
            #
            if not name:
                name = partner_name
            if partner_name and partner_name != name:
                if not street2:
                    street2 = street
                    street = name
                    name = partner_name
                elif is_standalone:
                    name = "%s / %s" % (partner_name,name)
            #
            # determine country
            country = data.get("country")
            country_id = None            
            if country:
                country_ids = self.pool.get("res.country").search(cr,uid,[("code","=",country)])
                country_id = country_ids and country_ids[0] or None
            # 
            # check if address is value
            if not name or not street or not city_zip or not city:
                return None
            
            link_obj = self.pool.get("edi.link")
            address_obj = self.pool.get("res.partner.address")            
            address_id = link_obj._local_id(cr,uid,system.id,address_obj._name,remote_id)
            create_link = not address_id          
            #
            vals = {
                  "name" : name,
                  "street" : street,
                  "street2" : street2,
                  "zip" : city_zip,
                  "city" : city,
                  "is_standalone" : is_standalone
              }
            if title_id:
                vals["title"]=title_id 
            if country_id:
                vals["country_id"]=country_id           
            #
            #search address            
            if not address_id:
                address_search = [("partner_id","=",partner.id),
                                  ("name","=",name),
                                  ("street","=",street),
                                  ("zip","=",city_zip),
                                  ("city","=",city)]
                if country_id:
                    address_search.append(("country_id","=",country_id))
                
                address_ids = address_obj.search(cr,uid,address_search)
                address_id = address_ids and address_ids[0] or None
                    
            # if modify is set than update address  
            if modify:                     
                #update address
                if address_id:              
                    address_obj.write(cr,uid,address_id,vals)
                    
                #create new address if type is not default
                if not address_id and address_type != "default":
                    # check if one delivery address exist,
                    # if not create default address also as deliver address
                    delivery_address_ids = address_obj.search(cr,uid,[("partner_id","=",partner.id),
                                               ("type","=",address_type)])
                    if not delivery_address_ids:
                        address = partner.address_id
                        if address:                        
                            address_obj.copy(cr,uid,address.id,{"type" : address_type})
                    
                    #
                    vals["partner_id"]=partner.id
                    vals["type"]=address_type
                    address_id = address_obj.create(cr,uid,vals)
                    #           
                    #
                #create link if it not exist
                if address_id and create_link:
                    link_obj.create(cr,uid, {
                        "name" : name,
                        "system_id" : system.id,
                        "local_model" : address_obj._name,
                        "local_id" : address_id,                    
                        "remote_model" : address_obj._name,
                        "remote_id" : remote_id 
                    })
                #            
        return address_id
    
    _name = "edi.profile"
    _description = "EDI Profile"
    _columns = {
        "name" : fields.related("system_id","name",type="char",size=128,store=False,readonly=True,string="Name"),
        "system_id" : fields.many2one("edi.system","System",required=True,select=True,ondelete="restrict"),
        "enabled" : fields.boolean("Enabled")
    }     
    _defaults = {
        "enabled" : 1
    }   
edi_profile()


class client_profile(osv.osv):
        
    def _profile_get(self,cr,uid,partner_id):
        profile_ids = self.search(cr,uid,[("system_id.partner_id","=",partner_id)])
        if profile_ids:        
            return self.browse(cr,uid,profile_ids[0])
        return None
    
    def _proxy_get(self, cr, uid, profile, context=None):
        if profile:
            return RPCProxy(profile.url, profile.database, profile.user, profile.password)
        return None
    
    def _profile_use(self,cr,uid,partner_id,context=None):
        profile = self._profile_get(cr, uid, partner_id)
        proxy = self._proxy_get(cr, uid, profile, context)
        return profile,proxy        
    
    _name = "edi.client_profile"
    _description = "EDI Client Profile"
    _inherit = "edi.profile"
    _columns = {
        "user" : fields.char("User",size=64,required=True),        
        "password" : fields.char("Password",size=64,required=True),
        "url" : fields.char("Url",size=128,required=True),
        "database" : fields.char("Database",size=64,required=True),
        "retry" : fields.boolean("Retry on Error")
    }       
    _defaults = {
        "retry" : True
    }
client_profile()


class server_profile(osv.osv):
    
    def _profile_get(self,cr,uid):
        profile_ids = self.search(cr,1,[("user_id","=",uid)])
        if profile_ids:        
            return self.browse(cr,1,profile_ids[0])
        raise osv.except_osv(_("Error"), _("Cannot find server profile"))
    
    def _client_mapped_user_id(self,cr,uid):
        profile_ids = self.search(cr,1,[("user_id","=",uid)])
        if profile_ids:            
            return self.read(cr,1,profile_ids[0],["property_mapped_user"])["property_mapped_user"][0]        
        raise osv.except_osv(_("Error"), _("Cannot find server profile"))
    
    def create(self, cr, uid, vals, context=None):        
        profile_id = super(server_profile,self).create(cr,uid,vals,context)
        profile = self.browse(cr,uid,profile_id,context)
        partner = profile.system_id.partner_id
        address = partner.address_id
        
        user_obj = self.pool.get("res.users")
        user_id = user_obj.create(cr,1,{
            "name" : "EDI %s" % (partner.name),
            "login" : "edi_%s" % (util.password(6),),
            "address_id" : address and address.id or None, 
            "password" : util.password(10),
            "groups_id" : [(6,0,[])]
        })        
        super(server_profile,self).write(cr, uid, profile_id, {"user_id" : user_id }, context)        
        return profile_id

        
    def write(self, cr, uid, ids, vals, context=None):
        ids = util.idList(ids)
        res = super(server_profile,self).write(cr, uid, ids, vals, context)
        user_obj = self.pool.get("res.users")
        for profile in self.browse(cr, uid, ids, context):
            user = profile.user_id            
            if user:
                partner = profile.system_id.partner_id
                address = partner.address_id
                user_obj.write(cr,1,user.id, {
                    "name" : "EDI %s" % (partner.name),
                    "address_id" : address and address.id or None 
                },context)        
        return res
    
    
    def unlink(self, cr, uid, ids, context):
        ids = util.idList(ids)
        user_obj = self.pool.get("res.users")
        for profile in self.browse(cr, uid, ids, context):
            user = profile.user_id            
            if user:
                user_obj.unlink(cr, 1, [user.id], context)
        return super(server_profile,self).unlink(cr,uid,ids,context)
            
            
    _name = "edi.server_profile"
    _description = "EDI Server Profile"   
    _inherit = "edi.profile"
    _columns = {        
        "user_id" : fields.many2one("res.users","User",readonly=True,select=True,ondelete="cascade"),
        "property_mapped_user" : fields.property("res.users",type="many2one",
                                           relation="res.users",

                                           view_load=True,
                                           group_name="EDI Properties",
                                           string="Mapped User",
                                           help="The user is used for system interaction, but could only used for a function \n"
                                                " where a user mapping is done."),
        "login" : fields.related("user_id","login",type="char",size=64,readonly=True,store=False,string="Login"),         
        "password" : fields.related("user_id","password",type="char",size=64,readonly=True,store=False,string="Password")
    }
server_profile()


class edi_remoteref(osv.osv):
            
    _name = "edi.remoteref"
    _description = "EDI Remote Reference"
    _columns = {
        "system_id" : fields.many2one("edi.system","System",ondelete="restrict",select=True),        
        "name" : fields.char("Remote Name",size=128,required=True,select=True),
        "remote_model" : fields.char("Remote Model",size=64,required=True,select=True),
        "remote_id" : fields.integer("Remote ID",required=True,select=True)
    }     
edi_remoteref()             


class edi_link(osv.osv):

    def _remote_id(self, cr, uid, system_id, local_model, local_id, remote_model=None):
        if local_id:
            if not remote_model:
                remote_model=local_model
            ids = self.search(cr, uid, [("system_id","=",system_id),("remote_model","=",remote_model),("local_model","=",local_model),("local_id","=",local_id)]) or None
            if ids:                
                return self.browse(cr, uid, ids[0]).remote_id                        
        return None
    
    def _unlink_remote_ids(self, cr, uid, system_id, remote_model, remote_id):
        if remote_id:
            ids = self.search(cr, uid, [("system_id","=",system_id),("remote_model","=",remote_model),("remote_id","=",remote_id)]) or None
            if ids:                
                self.unlink(cr, uid, ids)                            
    
    def _local_id(self, cr, uid, system_id, remote_model, remote_id, local_model=None):
        if remote_id:
            if not local_model:
                local_model=remote_model
            ids = self.search(cr, uid, [("system_id","=",system_id),("local_model","=",local_model),("remote_model","=",remote_model),("remote_id","=",remote_id)])
            if ids:
                model_obj = self.pool.get(local_model)
                if model_obj:
                    local_ids = model_obj.search(cr,uid,[("id","=",self.browse(cr, uid, ids[0]).local_id)])
                    if local_ids:
                        return local_ids[0]
        return None
    
    def _unlink_local_id(self, cr, uid, system_id, remote_model, remote_id, local_model=None):
        if remote_id:
            if not local_model:
                local_model=remote_model
            ids = self.search(cr, uid, [("system_id","=",system_id),("local_model","=",local_model),("remote_model","=",remote_model),("remote_id","=",remote_id)])
            if ids:
                self.unlink(cr, uid, ids)               
        
    _name = "edi.link"
    _description = "EDI Link"
    _columns = {
        "system_id" : fields.many2one("edi.system","System",ondelete="restrict",select=True),
        "name" : fields.char("Name",size=128,required=True,select=True),     
        "local_id" : fields.integer("Local ID",required=True,select=True),  
        "local_model" : fields.char("Model",size=64,required=True,select=True),
        "remote_model" : fields.char("Remote Model",size=64,required=True,select=True),
        "remote_id" : fields.integer("Remote ID",required=True,select=True)
    }
edi_link()


class edi_transfer(osv.osv):
    
    def _queue(self,cr,uid,partner_id,model,res_id,funct,context=None):
        client_profile_obj = self.pool.get("edi.client_profile")
        profile_ids = client_profile_obj.search(cr,uid,[("system_id.partner_id","=",partner_id)])
        if profile_ids: 
            profile = client_profile_obj.browse(cr,uid,profile_ids[0])           
            model_obj = self.pool.get(model)            
            names = model_obj.name_get(cr, uid, [res_id], context)
            if names:     
                vals = {
                    "name" : names[0][1],
                    "client_profile_id" : profile.id,
                    "model" : model,
                    "res_id" : res_id,
                    "function" : funct.__name__,
                    "error_log_id" : None              
                }                           
                self.create(cr, uid, vals, context)            
        
    
    def _call(self,cr,uid,partner_id,model,res_id,funct,context=None):
        client_profile_obj = self.pool.get("edi.client_profile")
        profile_ids = client_profile_obj.search(cr,uid,[("system_id.partner_id","=",partner_id)])
        if profile_ids: 
            profile = client_profile_obj.browse(cr,uid,profile_ids[0])
            proxy = client_profile_obj._proxy_get(cr,uid,profile,context=context)
            error_id = None
            ex = None
            if proxy:
                try:
                    funct(cr,uid,res_id,profile,proxy,context=context)
                except osv.except_osv,e:
                    ex = e
                    error_id = self.pool.get(model).log(cr, uid, res_id,_("EDI Transfer Error: %s") % (e.value,), error=True)                    
                except Exception,e:
                    ex = e
                    error_id = self.pool.get(model).log(cr, uid, res_id, _("Unexpected EDI Transfer Error"),error=True)
                    logger = netsvc.Logger()
                    logger.notifyChannel("edi_transfer", netsvc.LOG_ERROR,traceback.format_exc())                    
            if error_id and profile.retry:
                model_obj = self.pool.get(model)            
                names = model_obj.name_get(cr, uid, [res_id], context)
                if names:     
                    vals = {
                        "name" : names[0][1],
                        "client_profile_id" : profile.id,
                        "model" : model,
                        "res_id" : res_id,
                        "function" : funct.__name__,
                        "error_log_id" : error_id              
                    }                           
                    self.create(cr, uid, vals, context)
            elif ex:
                raise ex
                            
    def _process_transfers(self, cr, uid, *args):
        client_profile_obj = self.pool.get("edi.client_profile")
        transfer_ids = self.search(cr,uid,[("retry_count","<",60)],order="client_profile_id,model,res_id")

        model_obj = None
        model = None        
        client_profile = None
        
        
        for transfer in self.browse(cr, uid, transfer_ids):
            #
            if not client_profile or client_profile.id != transfer.client_profile_id.id:
                client_profile = transfer.client_profile_id
            #
            if model != transfer.model:
                model = transfer.model
                model_obj = self.pool.get(model)
            #
            res_ids = model_obj.search(cr,uid,[("id","=",transfer.res_id)])
            error_id = False
            if res_ids:
                res_id = res_ids[0]
                try:
                    if transfer.wait_count > 0:
                        self.write(cr, uid, transfer.id,{"wait_count" : transfer.wait_count-1 } )
                        continue
                    #
                    proxy = client_profile_obj._proxy_get(cr,uid,client_profile)
                    if proxy:
                        funct = transfer.function
                        if hasattr(model_obj,funct):
                            f = getattr(model_obj,funct)
                            f(cr,uid,res_id,client_profile,proxy)
                    #   
                except osv.except_osv,e:
                    error_id = model_obj.log(cr, uid, res_id,_("EDI Transfer Error: %s") % (e.value,), error=True)
                except Exception,e:
                    error_id = model_obj.log(cr, uid, res_id, _("Unexpected EDI Transfer Error"),error=True)
                    logger = netsvc.Logger()
                    logger.notifyChannel("edi_transfer", netsvc.LOG_ERROR,traceback.format_exc())                    
                 
            if not error_id or not client_profile.retry:
                self.unlink(cr, uid, transfer.id)
            else:
                retry_count = transfer.retry_count+1
                self.write(cr, uid, transfer.id,
                    {"retry_count" : retry_count,
                     "wait_count" : min(60,retry_count),
                     "error_log_id" : error_id } )
       
    _name = "edi.transfer"
    _description = "EDI Transfer"
    _columns = {
        "name" : fields.char("Name",size=128,required=True,select=True),
        "client_profile_id" : fields.many2one("edi.client_profile","Client",ondelete="cascade", select=True),
        "model" : fields.char("Model",size=64,required=True,select=True),
        "res_id" : fields.integer("Resource ID",required=True,select=True),
        "function" : fields.char("Function",size=64,required=True),
        "state" : fields.selection([("queued","Queued"),("failed","Failed")],"State",required=True,select=True),
        "error_log_id" : fields.many2one("res.log","Error Log",ondelete="set null",readonly=True),
        "retry_count" : fields.integer("Retry Count",select=True),
        "wait_count" : fields.integer("Wait Count")  
    }        
    _defaults = {
        "state" : "queued",
        "retry_count" : 0,
        "wait_count" : 0
    }     
edi_transfer()
