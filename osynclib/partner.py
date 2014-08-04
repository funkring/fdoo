# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
_logger = logging.getLogger(__name__)

def get_title_id(cl,title,cache=None):
    res = None
    if title:
        key = None
        if not cache is None:
            key = ("res.partner.title","title",title)
            res = cache.get(key)
        if res is None:
            title_obj=cl.get_model("res.partner.title")
            res = title_obj.search_id([("name","ilike",title),("domain","=","partner")])
            if key:
                cache[key]=res or 0
    return res

def get_country_id(cl,code,cache=None):
    res = None
    if code:
        key = None
        if not cache is None:
            key = ("res.country","code",code)
            res = cache.get(key)
        if res is None:
            country_obj=cl.get_model("res.country")
            res = country_obj.search_id([("code","ilike",code)])
            if key:
                cache[key]=res or 0
    return res

def get_city_id(cl,country_id,code,cache=None,create=False):
    res = None
    if code:
        key = None
        if not cache is None:
            key = ("res.city","country_code",country_id,code)
            res = cache.get(key)
        if res is None:
            city_obj=cl.get_model("res.city")
            res = city_obj.search_id([("country_id","=",country_id),("code","=",code)])
            if create and not res:
                res = city_obj.create({"country_id" : country_id, "code" : code})
            if key:
                cache[key]=res or 0
    return res


def get_partner_id(cl,values,parent_id=None,create=False,cache=None):
    partner_obj=cl.get_model("res.partner")
    ref = values.get("ref")
    name = values.get("name")    
    partner_id = None
    
    #check ref
    if ref:
        key = None
        if not cache is None:
            key = ("res.partner","ref",ref)
            partner_id=cache.get(key)
            
        if not partner_id:
            partner_id = partner_obj.search_id([("ref","=",ref)])
            if not partner_id and create:
                partner_id = partner_obj.create(values)
                _logger.info("created partner %s %s " % (ref,name))
            if key:
                cache[key]=partner_id
    #check contact           
    elif parent_id and name:
        key = None
        if not cache is None:
            key = ("res.partner","name",name)
            partner_id=cache.get(key)
            
        if not partner_id:
            partner_id = partner_obj.search_id([("parent_id","=",parent_id),("name","ilike",name)])
            if not partner_id:
                values["parent_id"]=parent_id
                values["is_company"]=False
                partner_id = partner_obj.create(values)
                _logger.info("created contact %s for partner with id %s" % (name,partner_id))
            if key:
                cache[key]=partner_id
    else:
        _logger.warn("no reference or parent_id with name passed for partner %s, unable to identify partner" % (name or "",))
        
    return partner_id
