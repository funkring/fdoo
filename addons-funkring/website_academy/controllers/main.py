# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.tools.translate import _
from openerp.addons.website.controllers.main import Website as controllers
controllers = controllers()

import logging
_logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
import time
from dateutil.relativedelta import relativedelta
from openerp import tools
import werkzeug.urls
from openerp.addons.website.models.website import slug
from openerp.tools.translate import _
import re

from openerp.addons.at_base import util
from datetime import datetime

from werkzeug.exceptions import BadRequest

try:
    import GeoIP
except ImportError:
    GeoIP = None
    _logger.warn("Please install GeoIP python module to use events localisation.")

UID_ROOT = 1
PATTERN_PRODUCT = re.compile("$product-([0-9]+)^")

class website_academy(http.Controller):
    
    @http.route(["/academy/validate/birthday"], type="http", auth="public", website=True)
    def validate_date(self, **kwargs):
        for value in kwargs.values():
            if not util.tryParseDate(value):
                return BadRequest()
        return ""
    
    @http.route(["/academy"], type="http", auth="public", website=True)
    def begin_registration(self, state_id=None, location_id=None, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context

        # conversions
        location_id = util.getId(location_id)
        state_id = util.getId(state_id)
        
        # used objects
        location_obj = request.registry["academy.location"]
        academy_product_obj = request.registry["academy.course.product"]
        state_obj = request.registry["res.country.state"]

        # default
        state_item = _("Select a State")
        location_item = _("Select a Location")

        # query
        cr.execute("SELECT p.state_id FROM academy_location l "
                   " INNER JOIN res_partner p ON p.id = l.address_id "
                   " GROUP BY 1 ")


        # get states
        state_ids = [r[0] for r in cr.fetchall()]
        state_ids = state_obj.search(cr, uid, [("id","in",state_ids)],order="name")

        states = state_obj.browse(cr, uid, state_ids, context=context)
        if state_id:
            state = state_obj.browse(cr, uid, state_id, context=context)
            if state:
                state_item = state.name


        # get location
        location_ids = []
        if state_id:
            location_ids = location_obj.search(cr, UID_ROOT, [("address_id.state_id","=",state_id)], order="name")

        locations = location_obj.browse(cr, UID_ROOT, location_ids, context=context)
        if location_id in location_ids:
            location = location_obj.browse(cr, UID_ROOT, location_id, context=context)
            if location:
                location_item = location.name



        # get products
        product_ids = academy_product_obj.search(cr, UID_ROOT, [])
        products = academy_product_obj.browse(cr, UID_ROOT, product_ids, context=context)

        # pack values
        values = {
            "states" : states,
            "state_item" : state_item,
            "state_id" : state_id,
            "locations" : locations,
            "location_item" : location_item,
            "location_id" : location_id,
            "products" : products
        }
        return request.website.render("website_academy.index", values)
    
    @http.route(["/academy/registration"], type="http", auth="public", website=True, methods=['GET'])
    def registration_get(self, state_id=None, location_id=None, **kwargs):
        return self.begin_registration(state_id, location_id)
    
    @http.route(["/academy/registration","/academy/registration/<int:stage_id>"], type="http", auth="public", website=True, methods=['POST'])
    def registration_post(self, stage_id, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        courses = []
        
        # used obj
        academy_product_obj = request.registry["academy.course.product"]
        uom_obj = request.registry["product.uom"]
        location_obj = request.registry["academy.location"]
        
        # build selection
        is_student_of_loc = False
        for key, value in kwargs.items():
            if key == "is_student_of_loc":
                is_student_of_loc = True
            else:
                m = PATTERN_PRODUCT.match(key)
                if m:
                    uom_id = util.getId(value)
                    if uom_id:
                        course_prod = academy_product_obj.browse(cr, UID_ROOT, util.getId(m.group(1)), context=context)
                        uom = uom_obj.browse(cr, UID_ROOT, uom_id, context=context)
                        courses.append((course_prod, uom))

        # finish registration        
        if stage_id==2:
            
            
            values = {}
            return request.website.render("website_academy.message", values)        
        else:
            # begin registration
            # location
            location_id = util.getId(kwargs.get("location_id"))
            location = location_id and location_obj.browse(cr, UID_ROOT, location_id, context=context) or None
            address = location and location.address_id
            location_lines = []
            if address:
                location_lines.append(address.name)
                if address.street:
                    location_lines.append(address.street)
                if address.street2:
                    location_lines.append(address.street2)
                if address.zip:
                    if address.city:
                        location_lines.append("%s %s" % (address.zip, address.city))
                    else:
                        location_lines.append(address.zip)
                
            values = {
                "courses" : courses,
                "location" : location,
                "location_lines" : location_lines,
                "is_student_of_loc" : is_student_of_loc,
                "location_id" : location_id
            }
            return request.website.render("website_academy.registration", values)
    
    
    