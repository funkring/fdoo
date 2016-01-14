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


from openerp.addons.at_base import extreport

class Parser(extreport.basic_parser):
    
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "pricelist_versions": self._pricelist_versions
        })
        
    def _pricelist_versions(self, o):
        version_obj = self.pool["product.pricelist.version"]
        if o._name == "product.pricelist.version":
            return [version_obj._pricelist_view(self.cr, self.uid, o, context=self.localcontext)]
        if o._name == "product.pricelist":
            version = o.active_version_id
            if version:
                return [version_obj._pricelist_view(self.cr, self.uid, version, context=self.localcontext)] 
        return []
        
        
        