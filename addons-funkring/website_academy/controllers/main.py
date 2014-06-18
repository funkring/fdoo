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
PATTERN_PRODUCT = re.compile("product-([0-9]+)")

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
    
    @http.route(["/academy/registration"], type="http", auth="public", website=True, methods=['POST'])
    def registration_post(self, **kwargs):
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
    
    @http.route(["/academy/register"], type="http", auth="public", website=True, methods=['POST'])
    def register(self, **kwargs):
         values = {}
         return request.website.render("website_academy.message", values)
    
    

#     @http.route(['/event', '/event/page/<int:page>'], type='http', auth="public", website=True)
#     def events(self, page=1, **searches):
#         cr, uid, context = request.cr, request.uid, request.context
#         event_obj = request.registry['event.event']
#         type_obj = request.registry['event.type']
#         country_obj = request.registry['res.country']
#
#         searches.setdefault('date', 'all')
#         searches.setdefault('type', 'all')
#         searches.setdefault('country', 'all')
#
#         domain_search = {}
#
#         def sdn(date):
#             return date.strftime('%Y-%m-%d 23:59:59')
#         def sd(date):
#             return date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
#         today = datetime.today()
#         dates = [
#             ['all', _('Next Events'), [("date_end", ">", sd(today))], 0],
#             ['today', _('Today'), [
#                 ("date_end", ">", sd(today)),
#                 ("date_begin", "<", sdn(today))],
#                 0],
#             ['week', _('This Week'), [
#                 ("date_end", ">=", sd(today + relativedelta(days=-today.weekday()))),
#                 ("date_begin", "<", sdn(today  + relativedelta(days=6-today.weekday())))],
#                 0],
#             ['nextweek', _('Next Week'), [
#                 ("date_end", ">=", sd(today + relativedelta(days=7-today.weekday()))),
#                 ("date_begin", "<", sdn(today  + relativedelta(days=13-today.weekday())))],
#                 0],
#             ['month', _('This month'), [
#                 ("date_end", ">=", sd(today.replace(day=1))),
#                 ("date_begin", "<", (today.replace(day=1) + relativedelta(months=1)).strftime('%Y-%m-%d 00:00:00'))],
#                 0],
#             ['nextmonth', _('Next month'), [
#                 ("date_end", ">=", sd(today.replace(day=1) + relativedelta(months=1))),
#                 ("date_begin", "<", (today.replace(day=1)  + relativedelta(months=2)).strftime('%Y-%m-%d 00:00:00'))],
#                 0],
#             ['old', _('Old Events'), [
#                 ("date_end", "<", today.strftime('%Y-%m-%d 00:00:00'))],
#                 0],
#         ]
#
#         # search domains
#         current_date = None
#         current_type = None
#         current_country = None
#         for date in dates:
#             if searches["date"] == date[0]:
#                 domain_search["date"] = date[2]
#                 if date[0] != 'all':
#                     current_date = date[1]
#         if searches["type"] != 'all':
#             current_type = type_obj.browse(cr, uid, int(searches['type']), context=context)
#             domain_search["type"] = [("type", "=", int(searches["type"]))]
#         if searches["country"] != 'all':
#             current_country = country_obj.browse(cr, uid, int(searches['country']), context=context)
#             domain_search["country"] = [("country_id", "=", int(searches["country"]))]
#
#         def dom_without(without):
#             domain = [('state', "in", ['draft','confirm','done'])]
#             for key, search in domain_search.items():
#                 if key != without:
#                     domain += search
#             return domain
#
#         # count by domains without self search
#         for date in dates:
#             if date[0] <> 'old':
#                 date[3] = event_obj.search(
#                     request.cr, request.uid, dom_without('date') + date[2],
#                     count=True, context=request.context)
#
#         domain = dom_without('type')
#         types = event_obj.read_group(
#             request.cr, request.uid, domain, ["id", "type"], groupby="type",
#             orderby="type", context=request.context)
#         type_count = event_obj.search(request.cr, request.uid, domain,
#                                       count=True, context=request.context)
#         types.insert(0, {
#             'type_count': type_count,
#             'type': ("all", _("All Categories"))
#         })
#
#         domain = dom_without('country')
#         countries = event_obj.read_group(
#             request.cr, request.uid, domain, ["id", "country_id"],
#             groupby="country_id", orderby="country_id", context=request.context)
#         country_id_count = event_obj.search(request.cr, request.uid, domain,
#                                             count=True, context=request.context)
#         countries.insert(0, {
#             'country_id_count': country_id_count,
#             'country_id': ("all", _("All Countries"))
#         })
#
#         step = 10  # Number of events per page
#         event_count = event_obj.search(
#             request.cr, request.uid, dom_without("none"), count=True,
#             context=request.context)
#         pager = request.website.pager(url="/event", total=event_count, page=page, step=step, scope=5)
#
#         order = 'website_published desc, date_begin'
#         if searches.get('date','all') == 'old':
#             order = 'website_published desc, date_begin desc'
#         obj_ids = event_obj.search(
#             request.cr, request.uid, dom_without("none"), limit=step,
#             offset=pager['offset'], order=order, context=request.context)
#         events_ids = event_obj.browse(request.cr, request.uid, obj_ids,
#                                       context=request.context)
#
#         values = {
#             'current_date': current_date,
#             'current_country': current_country,
#             'current_type': current_type,
#             'event_ids': events_ids,
#             'dates': dates,
#             'types': types,
#             'countries': countries,
#             'pager': pager,
#             'searches': searches,
#             'search_path': "?%s" % werkzeug.url_encode(searches),
#         }
#
#         return request.website.render("website_event.index", values)
#
#     @http.route(['/event/<model("event.event"):event>/page/<path:page>'], type='http', auth="public", website=True)
#     def event_page(self, event, page, **post):
#         values = {
#             'event': event,
#             'main_object': event
#         }
#         return request.website.render(page, values)
#
#     @http.route(['/event/<model("event.event"):event>'], type='http', auth="public", website=True)
#     def event(self, event, **post):
#         if event.menu_id and event.menu_id.child_id:
#             target_url = event.menu_id.child_id[0].url
#         else:
#             target_url = '/event/%s/register' % str(event.id)
#         if post.get('enable_editor') == '1':
#             target_url += '?enable_editor=1'
#         return request.redirect(target_url);
#
#     @http.route(['/event/<model("event.event"):event>/register'], type='http', auth="public", website=True)
#     def event_register(self, event, **post):
#         values = {
#             'event': event,
#             'main_object': event,
#             'range': range,
#         }
#         return request.website.render("website_event.event_description_full", values)
#
#     @http.route('/event/add_event', type='http', auth="user", methods=['POST'], website=True)
#     def add_event(self, event_name="New Event", **kwargs):
#         return self._add_event(event_name, request.context, **kwargs)
#
#     def _add_event(self, event_name=None, context={}, **kwargs):
#         if not event_name:
#             event_name = _("New Event")
#         Event = request.registry.get('event.event')
#         date_begin = datetime.today() + timedelta(days=(14))
#         vals = {
#             'name': event_name,
#             'date_begin': date_begin.strftime('%Y-%m-%d'),
#             'date_end': (date_begin + timedelta(days=(1))).strftime('%Y-%m-%d'),
#         }
#         event_id = Event.create(request.cr, request.uid, vals, context=context)
#         event = Event.browse(request.cr, request.uid, event_id, context=context)
#         return request.redirect("/event/%s/register?enable_editor=1" % slug(event))
#
#     def get_visitors_country(self):
#         GI = GeoIP.open('/usr/share/GeoIP/GeoIP.dat', 0)
#         return {'country_code': GI.country_code_by_addr(request.httprequest.remote_addr), 'country_name': GI.country_name_by_addr(request.httprequest.remote_addr)}
#
#     def get_formated_date(self, event):
#         start_date = datetime.strptime(event.date_begin, tools.DEFAULT_SERVER_DATETIME_FORMAT).date()
#         end_date = datetime.strptime(event.date_end, tools.DEFAULT_SERVER_DATETIME_FORMAT).date()
#         return ('%s %s%s') % (start_date.strftime("%b"), start_date.strftime("%e"), (end_date != start_date and ("-"+end_date.strftime("%e")) or ""))
#
#     @http.route('/event/get_country_event_list', type='http', auth='public', website=True)
#     def get_country_events(self ,**post):
#         if not GeoIP:
#             return ""
#         country_obj = request.registry['res.country']
#         event_obj = request.registry['event.event']
#         cr, uid, context,event_ids = request.cr, request.uid, request.context,[]
#         country_code = self.get_visitors_country()['country_code']
#         result = {'events':[],'country':False}
#         if country_code:
#             country_ids = country_obj.search(request.cr, request.uid, [('code', '=', country_code)], context=request.context)
#             event_ids = event_obj.search(request.cr, request.uid, ['|', ('address_id', '=', None),('country_id.code', '=', country_code),('date_begin','>=', time.strftime('%Y-%m-%d 00:00:00')),('state', '=', 'confirm')], order="date_begin", context=request.context)
#         if not event_ids:
#             event_ids = event_obj.search(request.cr, request.uid, [('date_begin','>=', time.strftime('%Y-%m-%d 00:00:00')),('state', '=', 'confirm')], order="date_begin", context=request.context)
#         for event in event_obj.browse(request.cr, request.uid, event_ids, context=request.context)[:6]:
#             if country_code and event.country_id.code == country_code:
#                 result['country'] = country_obj.browse(request.cr, request.uid, country_ids[0], context=request.context)
#             result['events'].append({
#                  "date": self.get_formated_date(event),
#                  "event": event,
#                  "url": event.website_url})
#         return request.website.render("website_event.country_events_list",result)
