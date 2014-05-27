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

class academy_trainer(osv.Model):
    _name = "academy.trainer"
    _description = "Academy Trainer"
    _inherits = {"res.partner" : "partner_id"}
    _columns = {
        "partner_id" : fields.many2one("res.partner", "Partner", required=True, ondelete="restrict"),
        "contract_ids" : fields.many2many("academy.contract", "academy_contract_trainer_rel", "contract_id", "trainer_id", "Contracts"),
        "active" : fields.boolean("Active"),
        "image" : fields.related("partner_id", "image", type="binary", relation="res.partner", string="Image")
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