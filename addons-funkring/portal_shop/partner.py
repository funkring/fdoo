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

class res_partner(models.Model):
    
    @api.model
    def default_get(self, fields_list):
        res = super(res_partner, self).default_get(fields_list)
        if "user_id" in fields_list and not "user_id" in res:
            user = self.env.user
            if user.has_group("portal_shop.group_sale_extern") and user.has_group("base.group_partner_manager"):
                res["user_id"] = self._uid                
        return res
        
    
    _inherit = "res.partner"
    
