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
    _inherit = "res.partner"
    
    download_count = fields.Integer("# Downloads", compute="_download_count", store=False)
    download_perm_ids = fields.One2many("portal.download.perm", "partner_id", "Download Permissions")
    
    @api.one
    def _download_count(self):        
        self.download_count = self.env["portal.download.perm"].search([('partner_id','=',self.id)], count=True)