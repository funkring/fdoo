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

from openerp.osv import fields, osv
from openerp.addons.at_base import util
from openerp.addons.at_base import extfields


class academy_year(osv.Model):
    _name = "academy.year"
    _columns = {
        "company_id" : fields.many2one("res.company","Company"),
        "name" : fields.char("Name", required=True, select=True),
        "semester_ids" : fields.one2many("academy.semester","year_id","Semester"),
        "date_start" : fields.date("Start", select=True),
        "date_end" : fields.date("End", select=True)
    }
    _defaults = {
        "company_id" : lambda self, cr, uid, context: self.pool.get("res.company")._company_default_get(cr, uid, "academy.year", context=context)
    }


class academy_semester(osv.Model):
    _name = "academy.semester"
    _columns = {
        "year_id" : fields.many2one("academy.year", "Year", ondelete="cascade", select=True),
        "name" : fields.char("Name", required=True),
        "date_start" : fields.date("Start", required=True),
        "date_end" : fields.date("End", required=True)
    }


class academy_student(osv.Model):

    def onchange_address(self, cr, uid, ids, use_parent_address, parent_id, context=None):
        return self.pool.get("res.partner").onchange_address(cr, uid, ids, use_parent_address, parent_id, context=context)

    def onchange_state(self, cr, uid, ids, state_id, context=None):
        return self.pool.get("res.partner").onchange_state(cr, uid, ids, state_id, context=None)

    _name = "academy.student"
    _inherits = {"res.partner":"partner_id"}
    _columns = {
        "partner_id" : fields.many2one("res.partner", "Partner", ondelete="restrict", required=True, select=True),
        "invoice_address_id" : fields.many2one("res.partner","Invoice Address"),
        "registration_ids" : fields.one2many("academy.registration","student_id","Registrations"),
        "tmp_partner_id" : extfields.duplicate("partner_id", "Partner", type="many2one", obj="res.partner")
    }
    _defaults = {
        "customer" : True
    }


class academy_location(osv.Model):
    _name = "academy.location"
    _inherits = {"resource.resource":"resource_id"}
    _columns = {
        "resource_id" : fields.many2one("resource.resource", "Resource", ondelete="restrict", required=True, select=True),
        "address_id" : fields.many2one("res.partner", "Address", ondelete="cascade"),
    }


class academy_course_product(osv.Model):

    def onchange_uom(self, cr, uid, ids, uom_id, uom_po_id):
        return self.pool.get("product.product").onchange_uom(cr, uid, ids, uom_id, uom_po_id)

    _name = "academy.course.product"
    _inherits = {"product.product":"product_id"}
    _columns = {
        "product_id" : fields.many2one("product.product", "Product", ondelete="restrict", required=True, select=True)
    }
    _defaults= {
        "sale_ok" : True,
        "type" : "service"
    }


class academy_registration(osv.Model):
    _name = "academy.registration"
    _description = "Academy Registration"
    _columns = {
        "year_id" : fields.many2one("academy.year", "Year", select=True),
        "student_id" : fields.many2one("academy.student", "Student", select=True),
        "location_id" : fields.many2one("academy.location", "Location", select=True),
        "course_prod_id" : fields.many2one("academy.course.product", "Product", select=True),
        "course_id" : fields.many2one("academy.course", "Course", select=True),
        "trainer_id" : fields.many2one("academy.trainer", "Trainer", select=True),
        "amount" : fields.float("Amount"),
        "uom_id" : fields.many2one("product.uom", "Unit", select=True),
        "state" : fields.selection([("draft","Draft"),
                                    ("cancel","Cancel"),
                                    ("registered","Registered"),
                                    ("assigned","Assigned"),
                                    ("open","Open"),
                                    ("paid","Paid")],
                                    "State")

    }

class academy_trainer(osv.Model):
    _name = "academy.trainer"
    _description = "Academy Trainer"
    _inherits = {"res.partner":"partner_id"}
    _columns = {
        "partner_id" : fields.many2one("res.partner", "Partner", required=True, ondelete="restrict"),
        "contract_ids" : fields.many2many("academy.contract", "academy_contract_trainer_rel", "contract_id", "trainer_id", "Contracts"),
    }
    _defaults = {
        "active" : True
    }


class academy_course(osv.Model):
    _name = "academy.course"
    _description = "Academy Course"
    _columns = {
        "name" : fields.char("Name", size=64, required=True),
        "description" : fields.text("Description"),
        "number" : fields.char("Number"),
        "date_from" : fields.datetime("Date from"),
        "date_to" : fields.datetime("Date to"),
        "topic_ids" : fields.one2many("academy.topic", "course_id", "Topics"),
        "trainer_ids" : fields.many2many("academy.trainer", "academy_trainer_course_rel", "trainer_id", "course_id", "Trainers"),
        "student_ids" : fields.many2many("res.partner", "partner_academy_course_rel", "course_id", "student_id", "Students"),

    }

class academy_topic(osv.Model):
    _name = "academy.topic"
    _description = "Academy Topic"
    _columns = {
        "name" : fields.char("Name", size=64, required=True),
        "course_id" : fields.many2one("academy.course", "Course", required=True),
        "description" : fields.text("Description"),
        "duration" : fields.float("Unit(s)"),
        "contract_ids" : fields.many2many("academy.contract", "academy_topic_contract_rel", "contract_id", "topic_id", "Contracts"),
    }


class academy_contract(osv.Model):
    _name = "academy.contract"
    _description = "Academy Contract"
    _columns = {
        "name" : fields.char("Name", size=64, required=True),
        "date" : fields.date("Closing Date"),
        "date_start" : fields.datetime("Date start"),
        "date_end" : fields.datetime("Date end"),
        "topic_ids" : fields.many2many("academy.topic", "academy_topic_contract_rel", "topic_id", "contract_id", "Courses"),
        "partner_id" : fields.many2one("res.partner", "Partner")
    }


class academy_journal(osv.Model):
    _name = "academy.journal"
    _description = "Academy Journal"

    def onchange_topic(self, cr, uid, ids, topic_id, context=None):
        res = {
            "value" : {}
        }

        if topic_id:
            topic = self.pool.get("academy.topic").browse(cr, uid, topic_id)
            res["value"]["name"] = str(topic.name)+"\n"+str(topic.description)
            res["value"]["duration"] = topic.duration
            res["value"]["course_id"] = topic.course_id.id

        return res

    _columns = {
        "name" : fields.text("Name"),
        "date" : fields.date("Date", required=True),
        "begin" : fields.float("Begin", help="The time must be between 00:00 and 24:00 o'clock and must not be bigger than the end"),
        "end" : fields.float("End", help="The time must be between 00:00 and 24:00 o'clock"),
        "topic_id" : fields.many2one("academy.topic", "Topic", required=True),
        "student_ids" : fields.many2many("res.partner", "res_partner_journal_rel", "partner_id", "journal_id", "Students"),
        "absence_ids" : fields.one2many("academy.journal.absence", "journal_id", "Absences"),
        "trainer_id" : fields.many2one("academy.trainer", "Trainer", required=True),
        "course_id" : fields.related("topic_id", "course_id", type="many2one", readonly=True, relation="academy.course", string="Course"),
        "duration" : fields.float("Unit(s)"),
        "expenses" : fields.float("Transport Expenses"),
        "place" : fields.char("Place", size=64)
    }

    _defaults = {
        "date" : util.currentDate(),
    }


class academy_journal_absence(osv.Model):
    _name = "academy.journal.absence"
    _description = "Academy Journal Absence"

    _columns = {
        "name" : fields.char("Reason", size=64, required=True),
        "time_from" : fields.float("From", help="The time must be between 00:00 and 24:00 o'clock and must not be bigger than the end"),
        "time_to" : fields.float("To", help="The time must be between 00:00 and 24:00 o'clock"),
        "partner_id" : fields.many2one("res.partner", "Partner"),
        "journal_id" : fields.many2one("academy.journal", "Journal"),
    }