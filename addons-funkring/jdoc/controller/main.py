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
from openerp.addons.web.http import Response

# from openerp.osv import osv
# from openerp import SUPERUSER_ID
# from openerp.tools.translate import _


class jdoc_controller(http.Controller):
    
    @http.route("/jdoc/attachment/<docid>/<name>", type="http", methods=["PUT","GET"], auth="user")
    def jdoc_attachment(self, session=None, **kwargs):
        """ Upload/Download attachment for jdoc 
            If session is applied, attachment is available after sync_commit of the session
        """
        return None
