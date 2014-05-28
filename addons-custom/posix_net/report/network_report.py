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

from osv import orm
from report import report_sxw

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        
        super(Parser, self).__init__(cr, uid, name, context=context) #instead of 'ids' name?
        self.localcontext.update({
            "lines": self.lines,
            "units": self.units
        })
    
    def lines(self):
        lines = []
        cols = []
        lines.append(cols)
        for obj in self.objects:
            if len(cols) >= 2:
                cols=[]
                lines.append(cols)
            cols.append(obj)
        return lines
        
    def units(self, line, col):
        value = {
            "email" : "",
            "pass" : ""        
        }
        
        if col < len(line):
            unit = line[col]
            value["unit"]=unit
            node = unit.address_id
            if node.email:
                value["email"]=node.email
            if unit.password:
                value["pass"]=unit.password
        else:
            value["unit"] = orm.browse_null()
        
        return value        
        
        