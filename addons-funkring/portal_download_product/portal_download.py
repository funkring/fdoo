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

from openerp import models, fields, api, _

class portal_download(models.Model):
    _inherit = "portal.download"
    _order = "product_id, name"
    
    product_id = fields.Many2one("product.product", "Product", ondelete="restrict", copy=True, index=True)
    
    
    @api.multi
    def name_get(self):
        names = []
        
        for obj in self:
            product =  obj.product_id
            name = obj.name
            if product and product.default_code:
                name = "[%s] %s" % (product.default_code, name)
            names.append((obj.id, name))
        
        return names
    
    def _name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100, name_get_uid=None):
        if not (name == '' and operator == 'ilike'):
            if not args:
                args = []
            args  = ["|","|",("product_id.name", operator, name),("product_id.default_code", operator, name)] + args
        return super(portal_download, self)._name_search(cr, user, name, args, operator, context, limit, name_get_uid)
