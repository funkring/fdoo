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

import re
from openerp import models, fields, api, _


class UtilFile(models.AbstractModel):
    _name = "util.file"

    def _cleanFileName(self, name):
        repl_map = {
                "Ö" : "Oe",
                "Ü" : "Ue",
                "Ä" : "Ae",
                "ö" : "oe",
                "ü" : "ue",
                "ä" : "ae"
        }
    
    
        for key,value in repl_map.iteritems():
            name = name.replace(key,value)
    
        name = name.replace(", ","_")
        name = name.replace(" ","_")
        name = re.sub("[^a-zA-Z0-9\-_ ,]","",name)
        return name
