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
    
    def __init__(self, proxy, name):
        self.name=name
        self.proxy=proxy

    def execute(self, *args, **kwargs):
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
    def __init__(self, con, obj):
        self.model_name = obj
        self.connection = con
        auth = BasicAuth(self.connection.user, self.connection.password)        
        self.resource = Resource("%s/rest/object/%s/%s" % (self.connection.url, self.connection.database, obj), filters=[auth], basic_auth_url=True)
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: Execute(self,name).execute(*args, **kwargs)
    
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, context=None):
        """
        A shortcut method to combine a search() and a read().

        :param domain: The domain for the search.
        :param fields: The fields to extract (can be None or [] to extract all fields).
        :param offset: The offset for the rows to read.
        :param limit: The maximum number of rows to read.
        :param order: The order to class the rows.
        :param context: The context.
        :return: A list of dictionaries containing all the specified fields.
        """
        record_ids = self.search(domain or [], offset, limit or False, order or False, context or {})
        if not record_ids: return []
        records = self.read(record_ids, fields or [], context or {})
        return records


class RPCProxy(object):
    def __init__(self, url, database, user, password):
        self.database=database
        self.password=password
        self.url=url
        self.user=user
        self.user_context = None
                
    def get_model(self, obj):
        return RPCProxyOne(self, obj)
    
    def get(self, obj):
        return self.get_model(obj)    
    
    def get_user_context(self):
        """
        Query the default context of the user.
        """
        if not self.user_context:
            self.user_context = self.get_model('res.users').context_get()
        return self.user_context
    

if __name__ == '__main__':
    proxy = RPCProxy("http://localhost:8069","inred","admin","**")
    proxy_category_obj = proxy.get_model("product.category")
    ids = proxy_category_obj.search([])    
    res = proxy_category_obj.name_get(ids)
    print str(res)
    