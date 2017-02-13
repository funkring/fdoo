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
    _name = "portal.download"
    _description = "Download"
    _order = "name"
    
    @api.one
    def _compute_download_link(self):
        self.download_link='<a href="/portal_download/start/%s">%s</a>' % self.name_get()[0]
        
    @api.multi
    def action_download(self):
        for download in self:
            url = "/portal_download/start/%s" % self.id
            return {
               'name': _('Document Download'),
               'type': 'ir.actions.act_url',
               'url': url,
               'target': 'self'
            }

    
    name = fields.Char("Name", required=True, index=True)
    code = fields.Char("Code", help="Download code which can be used for identifying or as shortcut")
    permission_ids = fields.One2many("portal.download.perm", "download_id", "Permissions")
    download_link = fields.Html("Download Link",compute="_compute_download_link") 
    active = fields.Boolean("Active", default=True)
    
    
class portal_download_perm(models.Model):
    _name = "portal.download.perm"
    _description = "Download Permission"
    
    partner_id = fields.Many2one("res.partner","Partner", required=True, ondelete="cascade")
    download_id = fields.Many2one("portal.download","Download",required=True, ondelete="cascade")
    download_count = fields.Integer("Download Count",readonly=True)
    