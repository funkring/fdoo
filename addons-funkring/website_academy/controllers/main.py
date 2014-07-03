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

PATTERN_PRODUCT = re.compile("^product-([0-9]+)$")

class website_academy(http.Controller):
    
    @http.route(["/academy/validate/birthday"], type="http", auth="public", website=True)
    def validate_date(self, **kwargs):
        for value in kwargs.values():
            if not util.tryParseDate(value):
                return BadRequest()
        return ""
    
    def get_hidden_user(self):
        public_user = request.registry["res.users"].browse(request.cr, request.uid, request.uid, context=request.context)
        hidden_user = public_user.company_id.academy_webuser_id or public_user
        return hidden_user
    
    @http.route(["/academy"], type="http", auth="public", website=True)
    def begin_registration(self, state_id=None, location_id=None, zip_code=None, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        hidden_uid = self.get_hidden_user().id
        
        # conversions
        location_id = util.getId(location_id)
        state_id = util.getId(state_id)
        
        # used objects
        location_obj = request.registry["academy.location"]
        academy_product_obj = request.registry["academy.course.product"]
        state_obj = request.registry["res.country.state"]
        city_obj = request.registry["res.city"]

        # default
        state_item = _("Select a State")
        location_item = _("Select a Location")
        zip_item = _("Select District")

        # query
        cr.execute("SELECT p.state_id, COUNT(p.id) AS schools FROM academy_location l "
                   " INNER JOIN res_partner p ON p.id = l.address_id "
                   " GROUP BY 1 "
                   " ORDER BY schools DESC")


        # get states
        state_ids = [r[0] for r in cr.fetchall()]
        states = state_obj.browse(cr, uid, state_ids, context=context)
        if state_id:
            state = state_obj.browse(cr, uid, state_id, context=context)
            if state:
                state_item = state.name

        # get districts
        zip_list = []
        zip_sel = None
        if state_id:
            # query
            cr.execute("SELECT p.zip, c.name FROM academy_location l "
                       " INNER JOIN res_partner p ON p.id = l.address_id "
                       " INNER JOIN res_city c ON c.state_id = p.state_id AND c.code = p.zip "
                       " WHERE p.state_id = %s"
                       " GROUP BY 1, 2 "
                       " ORDER BY c.name ", (state_id,))
            zip_list = [(r[0], "%s %s" % (r[0],r[1])) for r in cr.fetchall()]
                        
            for zip_val in zip_list:
                if zip_val[0]==zip_code:
                    zip_sel=zip_val
                    break
        
        # validate districts
        if zip_sel:
            zip_code, zip_item = zip_sel
        else:
            zip_code = None

        # get location
        location_ids = []
        if state_id and zip_code:
            search = [("address_id.state_id","=",state_id)]
            if zip_code:
                search.append(("address_id.zip","=",zip_code))
            location_ids = location_obj.search(cr, hidden_uid, search, order="name")

        locations = location_obj.browse(cr, hidden_uid, location_ids, context=context)
        if location_id in location_ids:
            location = location_obj.browse(cr, hidden_uid, location_id, context=context)
            if location:
                location_item = location.name

        # get products
        product_ids = academy_product_obj.search(cr, hidden_uid, [])
        products = academy_product_obj.browse(cr, hidden_uid, product_ids, context=context)

        # pack values
        values = {
            "states" : states,
            "state_item" : state_item,
            "state_id" : state_id,
            "locations" : locations,
            "location_item" : location_item,
            "location_id" : location_id,
            "products" : products,
            "zip_item" : zip_item,
            "zip_list" : zip_list
        }
        return request.website.render("website_academy.index", values, context=context)
    
    @http.route(["/academy/registration","/academy/registration/<int:stage>"], type="http", auth="public", website=True, methods=['GET'])
    def registration_get(self, state=None, location_id=None, **kwargs):
        return self.begin_registration(state_id, location_id)
    
    @http.route(["/academy/registration","/academy/registration/<int:stage>"], type="http", auth="public", website=True, methods=['POST'])
    def registration_post(self, stage=1, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        hidden_uid = self.get_hidden_user().id
        
        courses = []
        
        # used obj
        academy_product_obj = request.registry["academy.course.product"]
        uom_obj = request.registry["product.uom"]
        location_obj = request.registry["academy.location"]
        student_obj = request.registry["academy.student"]
        partner_obj = request.registry["res.partner"]
        city_obj = request.registry["res.city"]
        reg_obj = request.registry["academy.registration"]
        
        # build selection
        is_student_of_loc = False
        parent_address = True
        invoice_address = False
        for key, value in kwargs.items():
            if key == "is_student_of_loc":
                is_student_of_loc = True
            elif key == "has_legal_age":
                parent_address = False
            elif key == "has_invoice_address":
                invoice_address = True                
            else:
                m = PATTERN_PRODUCT.match(key)
                if m:
                    uom_id = util.getId(value)
                    if uom_id:
                        course_prod = academy_product_obj.browse(cr, hidden_uid, util.getId(m.group(1)), context=context)
                        uom = uom_obj.browse(cr, hidden_uid, uom_id, context=context)
                        courses.append((course_prod, uom))
                        
        # location
        location_id = util.getId(kwargs.get("location_id"))
        location = location_id and location_obj.browse(cr, hidden_uid, location_id, context=context) or None
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
        
        # registration 
        registration = kwargs.get("registration")
        if registration:
            reg_id = reg_obj.search_id(cr, hidden_uid, [("name","=",registration)], context=context)
            if reg_id:
                values = {
                    "message_title" : _("Registration already finished!"),
                    "message_text" :  _("<p>Registration %s was done</p>") % registration                                  
                }
                return request.website.render("website_academy.message", values, context=context)        
       
        # handle stage
        if stage==2:
            # finish registration
            warnings = []
            messages = []
            #
            def create_address(obj, fields, data, name):
                """ get address or create new 
                    :return (id,Name)
                """
                # search address
                address_id = obj.search_id(cr, hidden_uid, [("name","=",data.get("name")),("email","=",data.get("email"))])
                if address_id:
                    cur_data = obj.read(cr, hidden_uid, address_id, fields, context=context)
                    changes=[]
                    fields = obj.fields_get(cr, hidden_uid, allfields=fields, context=context)
                    for key, value in cur_data.items():
                        if key == "id":
                            continue                        
                        value1 = value or ""
                        value2 = data.get(key) or ""
                        
                        # get name if it is a many2one field
                        if isinstance(value1,tuple):
                            value1=value1[1]                            
                        if isinstance(value2,tuple):
                            value2=value2[1]                        
                        if value1 != value2:
                            changes.append(_("Value of field '%s' is '%s' but customer typed '%s'") % (fields[key]["string"],value1,value2))
                    if changes:
                        warnings.append("<p><b>%s</b></p>" % name)
                        for change in changes:
                            warnings.append("<p>%s</p>" % change)
                        warnings.append("<p></p>")                                                
                else:
                    # convert tuple to id
                    for key, value in data.items():
                        if isinstance(value,tuple):
                            data[key]=value[0]

                    # create new address
                    address_id = obj.create(cr, hidden_uid, data, context=context)
                    
                if address_id:
                    return obj.name_get(cr, hidden_uid, [address_id], context=context)[0]                    
                return None
            
            def get_address(prefix):
                """ parse address data """
                # simple get
                def get(name):
                    arg =  kwargs.get("%s_%s" % (prefix,name))
                    return arg and arg.strip() or ""
                
                firstname = get("firstname")
                lastname = get("lastname")
                email = get("email")
                
                if not firstname or not lastname or not email:
                    return None
                
                name =  "%s %s" % (lastname, firstname)
                city = get("city")
                zip = get("zip")
                res = {
                    "name" : name,
                    "email": email,
                    "street" : get("street"),
                    "zip" : zip,
                    "city" : city
                }  

                nationality = get("nationality")
                if nationality:
                    res["nationality"]=nationality

                birthday_dt, birthday = util.tryParseDate(get("birthday"))
                if birthday_dt:
                    res["birthday"] = util.dateToStr(birthday_dt)
                    
                phone = get("phone")
                if phone:
                    res["phone"] = phone
                
                city_values = city_obj.search_read(cr, hidden_uid, [("code","=",zip)], ["name","state_id"], context=context)                
                for city_val in city_values:
                    if re.sub("[^A-Za-z]", "", city) == re.sub("[^A-Za-z]", "", city_val["name"]):
                        res["state_id"] = city_val["state_id"]
                        res["city"] = city_val["name"]
                        break
                    
                return res              
               
               
            if not courses:
                raise osv.except_osv(_("Error"), _("No courses selected"))
               
            student_values = get_address("student")
            if not student_values:
                raise osv.except_osv(_("Error"), _("No student address passed"))
                        
            if parent_address:
                parent_values = get_address("parent")
                if not parent_values:
                    raise osv.except_osv(_("Error"), _("No parent address passed"))
                student_values["parent_id"]=create_address(partner_obj, ["name","email","street","zip","city","phone","birthday"], 
                                                           parent_values, _("Parent"))
            invoice_address_id = None
            if invoice_address:
                invoice_values = get_address("invoice")
                if not invoice_values:
                    raise osv.except_osv(_("Error"), _("No invoice address passed"))
                invoice_address_id=create_address(partner_obj, ["name","email","street","zip","city","phone"], 
                                                                    invoice_values, _("Invoice Address"))[0]
            

            # create student address            
            student = create_address(student_obj,
                                     ["name","email","street","zip","city","phone","nationality","birthday","parent_id"],
                                     student_values, _("Student"))
            
            # create courses                               
            for course in courses:

                values = {
                    "course_prod_id" : course[0].id,
                    "uom_id" : course[1].id,
                    "student_id" : student[0],
                    "location_id" : location_id,
                    "student_of_loc" : is_student_of_loc
                }
                
                # set invoice address id
                if invoice_address_id:
                    values["invoice_address_id"]=invoice_address_id
                
                # set registration number
                if registration:
                    values["name"]=registration
                    registration=None
                
                # create, register and commit
                reg_id = reg_obj.create(cr, hidden_uid, values, context=context)
                reg_name = reg_obj.read(cr, hidden_uid, reg_id, ["name"], context=context)["name"]                         
                reg_obj.do_register(cr, hidden_uid, [reg_id], check=True, context=context)
                cr.commit()       
                
                # create status message
                messages.append(_("<p>Registration %s was created.</p>") % reg_name)
                
                # add info if something is to add
                if warnings:
                    warnings = "\n".join(warnings)
                    reg_obj.message_post(cr, hidden_uid, reg_id, body=warnings, context=context)
            
            values = {
                "message_title" : _("Registration finished!"),
                "message_text" : "\n".join(messages)                                   
            }
            return request.website.render("website_academy.message", values, context=context)        
        else:
            # begin registration
            values = {
                "courses" : courses,
                "location" : location,
                "location_lines" : location_lines,
                "is_student_of_loc" : is_student_of_loc,
                "location_id" : location_id,
                "registration" : reg_obj._next_sequence(cr, hidden_uid, context) 
            }
            return request.website.render("website_academy.registration", values)
    
    
    