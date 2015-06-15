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

class res_partner(osv.Model):
    
    def unlink(self, cr, uid, ids, context=None):
        ids = util.idList(ids)     
        user_ids = set()
        
        context = context and dict(context) or {}
        context["active_test"]=False
        
        for partner in self.browse(cr, uid, ids, context=context):            
            for user in partner.user_ids:
                if not user.active or user.share:
                    user_ids.add(user.id)
       
        user_ids = list(user_ids)
        if user_ids:
            user_obj = self.pool["res.users"]
            user_obj.unlink(cr, uid, user_ids, context=context)     
                     
        super(res_partner,self).unlink(cr, uid, ids, context=context)
        
               
        
    _inherit = "res.partner"
    _columns = {        
        "education_ids" : fields.one2many("eagency.client.education", "partner_id", "Education"),
        "skill_ids" : fields.many2many("eagency.skill", "eagency_partner_skill_rel", "partner_id", "skill_id", "Skills"),
        "education" : fields.text("Additional Education"),     
        "prof_status_id" : fields.many2one("eagency.prof.status", "Professional Status"),
        "lang_skill_ids" : fields.one2many("eagency.lang.skill", "partner_id", "Language Skills"),
        "lang_other" : fields.char("Other language skills"),
        "preferred_area_ids" : fields.many2many("eagency.area", "eagency_partner_area_rel", "partner_id", "area_id", "Areas", required=True),
        "special_requirements" : fields.text("Special Requirements"),
        "motivation" : fields.text("Motivation",help="Important conditions and other")
    }


class eagency_client_education(osv.Model):

    _name = "eagency.client.education"
    _rec_name = "education_id"
    _columns = {
        "partner_id" : fields.many2one("res.partner", "Client", invisible=True, required=True, ondelete="cascade"),
        "completed" : fields.integer("Graduation date", required=True),
        "country_id" : fields.many2one("res.country", "Graduation country", required=True),
        "education_id" : fields.many2one("eagency.education", "Education", required=True),
    }


class eagency_education(osv.Model):

    _name = "eagency.education"
    _columns = {
        "name" : fields.char("Name", size=64, required=True, translate=True),
        "code" : fields.char("Code", size=8)
    }
    

class eagency_skill(osv.Model):

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ["name", "parent_id"], context=context)
        res = []
        for record in reads:
            name = record["name"]
            if record["parent_id"]:
                name = record["parent_id"][1] + " / " + name
            res.append((record["id"], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _name = "eagency.skill"
    _rec_name = "complete_name"
    _columns = {
        "complete_name" : fields.function(_name_get_fnc, method=True, type="char", size=256, string="Name", select=True),
        "name" : fields.char("Name", size=64, required=True, translate=True),
        "parent_id" : fields.many2one("eagency.skill", "Parent"),
    }
    _order = "name"
    

class eagency_prof_status(osv.Model):

    _name = "eagency.prof.status"
    _columns = {
        "name" : fields.char("Name", required=True, size=64, translate=True),
        "sequence" : fields.integer("Sequence")
    }
    _order = "sequence, name"


class eagency_area(osv.Model):

    _name = "eagency.area"
    _columns = {
        "name" : fields.char("Name", required=True, size=64, translate=True),
        "country_ids" : fields.many2many("res.country", "eagency_area_country_rel", "area_id", "country_id", "Countries"),
        "sequence" : fields.integer("Sequence")
    }
    _order = "sequence, name"


class eagency_lang(osv.Model):

    _name = "eagency.lang"
    _columns = {
        "name" : fields.char("Name", required=True, size=64, translate=True),
        "lang_id" : fields.many2one("res.lang", "Language", required=True),
        "sequence" : fields.integer("Sequence")
    }
    _order = "sequence, name"


class eagency_lang_skill(osv.Model):

    _name = "eagency.lang.skill"
    _rec_name = "language_id"

    _columns = {
        "language_id" : fields.many2one("eagency.lang", "Language", required=True),
        "skill" : fields.selection([("none", "None / Few"), ("intermediate", "Intermediate"),
                                    ("fluent", "Fluent"), ("mother_language", "Mother language")], "Skill", required=True),
        "partner_id" : fields.many2one("res.partner", "Client", invisible=True, required=True, ondelete="cascade")
    }

