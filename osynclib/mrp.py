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

def get_workcenter(cl, values, create=False, cache=None):
    code = values.get("code")
    if not code:
        return None
        
    key = None
    res = None
    if cache:
        key = ("mrp.workcenter","code",code)
        res = cache.get(key,None)
    
    if res is None or (not res and create):        
        workcenter_obj = cl.get_model("mrp.workcenter")
        res = workcenter_obj.search_id([("code","=",code)])
        if not res and create: 
            res = workcenter_obj.create(values)

        if key:
            cache[key]=res or False
        
    return res