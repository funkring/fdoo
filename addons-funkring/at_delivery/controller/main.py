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

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.web.controllers.main import content_disposition

import base64

class delivery_helper(http.Controller):
        
    @http.route(["/picking/<int:picking_id>/label.pdf"], type="http", auth="user")
    def picking_download(self, picking_id, **kwargs):
        picking_obj = request.registry["stock.picking"]
        cr, uid, context = request.cr, request.uid, request.context
        
        picking = picking_obj.browse(cr, uid, picking_id, context=context)
        
        label_name = picking.carrier_label_name
        label = picking.carrier_label
        
        if not label or not label_name:
            return request.not_found()
        
        pdfdata = base64.b64decode(label)
        return request.make_response(pdfdata,
            [('Content-Type', 'application/pdf'),
             ('Content-Disposition', content_disposition(label_name))])       