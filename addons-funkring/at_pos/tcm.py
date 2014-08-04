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

#from openerp.osv import fields,osv

HIGHEST_PRIORITY = 255
MEDIUM_PRIORITY = 127
LOWEST_PRIORITY = 1
NO_PRIORITY = 0

STATE_UNKNOWN = 0
STATE_CASH_STMT_OPENING = 1
STATE_ORDER = 2
STATE_CASH_STMT_BALANCING = 3
STATE_CASH_STMT_CLOSED = 4
STATE_CASH_STMT_NONE = 5


def tcm_name(obj):
    if obj:
        return {"id" : obj.id,
                "name" : obj.name or "" 
               }
    return None

def tcm_status(obj,descriptions=None):
    res = tcm_name(obj)
    if res:
        res["state"]=obj.state
        description = descriptions.get(obj.state)
        if description:
            res["description"]=description[1]
            res["priority"]=description[0]
    return res
        