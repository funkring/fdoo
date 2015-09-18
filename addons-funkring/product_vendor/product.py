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

from openerp.osv import fields, osv
from openerp.addons.at_base import util

class product_template(osv.osv):
    
    def _product_vendor_name(self, name2, vendor):
        if vendor:
            return "%s %s" % (vendor, name2)
        return name2
    
    def create(self, cr, uid, vals, context=None):
        if "name2" in vals:
            vals["name"] = self._product_vendor_name(vals.get("name2"), vals.get("manufacturer"))
        return super(product_template, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if "name2" in vals or "manufacturer" in vals:
            ids = util.idList(ids)
            for oid in ids:
                vals_tmp = self.read(cr, uid, oid, ["name2","manufacturer"], context=context)
                vals_tmp.update(vals)
                vals_tmp["name"] = self._product_vendor_name(vals_tmp.get("name2"), vals_tmp.get("manufacturer"))
                super(product_template, self).write(cr, uid, oid, vals_tmp, context=context)
            return True
        
        return super(product_template, self).write(cr, uid, ids, vals, context=context)
    
    _inherit = "product.template"
    _columns = {
        "manufacturer" : fields.char("Manufacturer"),
        "name2": fields.char("Name", required=True, translate=True, select=True)
    }
    
    