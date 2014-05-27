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

import logging
_logger = logging.getLogger(__name__)

def get_uom_id(cl,values,cache=None,create=False):
    code = values.get("code")
    name = values.get("name")
    uom_id = None
    key = None
    if code:
        if not cache is None:
            key  = ("product.uom","code",code)
            uom_id=cache.get(key)
        if not uom_id:
            uom_obj=cl.get_model("product.uom")
            uom_id=uom_obj.search_id([("code","=",code)])
            if uom_id and key:
                cache[key]=uom_id                
    if not uom_id and name:
        if not cache is None:
            key = ("product.uom","name",name)
            uom_id=cache.get(key)
        if not uom_id:
            uom_obj=cl.get_model("product.uom")
            uom_id=uom_obj.search_id([("name","=",code)])
            if uom_id and key:
                cache[key]=uom_id

    #create new
    if create and not uom_id and name:
        uom_categ_obj=cl.get_model("product.uom.categ")
        categ_id = uom_categ_obj.search_id([("name","=",name)])
        if not categ_id:
            categ_id = uom_categ_obj.create({"name" : name})
            
        uom_obj=cl.get_model("product.uom")
        uom_id = uom_obj.create({
            "name" : name,
            "code" : code,
            "category_id" : categ_id,
            "factor" : 1.0,
            "uom_type" : "reference"
        })
        
        if cache and key:
            cache[key]=uom_id
            
    return uom_id
                           

def get_product_id(cl,values,create=False,update=False,cache=None):
    code = values.get("default_code")
    name = values.get("name")
    product_id = None
    if code:
        key = None
        if not cache is None:
            key = ("product.product","code",code)
            product_id=cache.get(key)
            
        if not product_id:
            product_obj=cl.get_model("product.product")
            product_id = product_obj.search_id([("default_code","=",code)])
            if not product_id and (create or update):
                product_id = product_obj.create(values)
                _logger.info("created product %s %s " % (code,name))
            if product_id and update:
                product_obj.write(product_id,values,context={"uom_category_check_disabled" : True })
            if key:
                cache[key]=product_id
    else:
        _logger.warn("no code passed for product %s, unable to identify product" % (name or "",))
    return product_id
    
