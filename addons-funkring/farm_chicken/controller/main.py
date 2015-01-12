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


import logging

from openerp import http
from openerp.http import request
from openerp.addons.web.controllers.main import login_redirect
import simplejson

_logger = logging.getLogger(__name__)

class AnalyzerController(http.Controller):
    ''' It was a try with sencha and openerp, but not finished yet !!! '''
    
    def resp_json(self, request, data):
        res = simplejson.dumps(data)
        resp = request.make_response(res,
                        headers=[("Cache-Control","no-cache"),
                                 ("Content-Type","application/json")])
        return resp
        

    @http.route("/farm_chicken/static/src/analyzer/index.html", type="http", auth="user")
    def index(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session

        if not session.uid:
            return login_redirect()

        html = request.registry.get("ir.ui.view").render(cr, session.uid,'farm_chicken.analyzer_index',{})
        return html
    
    @http.route("/farm_chicken/analyzer/production.json", type="http", auth="user")
    def productions(self, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
                
        if not session.uid:
            res = []
        else:
            logbook_obj = request.registry.get("farm.chicken.logbook")
            res = logbook_obj.search_read(cr, session.uid, [], ["name"], context=context)
            
        res = self.resp_json(request,res)
        return res
