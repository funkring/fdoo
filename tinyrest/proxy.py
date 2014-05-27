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

from restkit import Resource, BasicAuth
from StringIO import StringIO
import json


#http://devkit1:8069/rest/object/funkring/res.users/execute?funct=%27whoami%27
class Execute(object):
    def __init__(self,proxy,name):
        self.name=name
        self.proxy=proxy

    def execute(self,*args,**kwargs):
        res_str = None
        #do get if no params
        if not args and not kwargs:            
            res = self.proxy.resource.get("/execute",params_dict={"funct" : repr(self.name)})
            res_str = res.body_string()
            
        #otherwise post
        else:
            params = {"funct" : repr(self.name), 
                      "_*args" : None }
                     
            for key in kwargs:
                params[key]=repr(kwargs[key])
            
            payload_io = StringIO()
            json.dump(args,payload_io)
            payload = payload_io.getvalue()
           
            res = self.proxy.resource.post("/execute",payload=payload,params_dict=params)                
            res_str = res.body_string()             
            
        if res_str:
            if "OK" == res_str:
                return True
            else:
                return json.loads(res_str)
        return False
        


class RPCProxyOne(object):
    def __init__(self, url, database, user, password, obj):
        self.database=database
        self.url=url
        auth = BasicAuth(user,password)        
        self.resource=Resource("%s/rest/object/%s/%s" % (url,database,obj),filters=[auth],basic_auth_url=True)
    def __getattr__(self, name):
        return lambda *args, **kwargs: Execute(self,name).execute(*args, **kwargs)


class RPCProxy(object):
    def __init__(self, url, database, user, password):
        self.database=database
        self.password=password
        self.url=url
        self.user=user
    def get(self, obj):
        return RPCProxyOne(self.url, self.database, self.user, self.password, obj)
    

if __name__ == '__main__':
    proxy = RPCProxy("http://localhost:8069","inred","admin","**")
    proxy_category_obj = proxy.get("product.category")
    ids = proxy_category_obj.search([])    
    res = proxy_category_obj.name_get(ids)
    print str(res)
    