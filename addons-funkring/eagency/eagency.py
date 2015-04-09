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

class eagency_client(osv.Model):

    _name = "eagency.client"
    _inherits = {"res.partner" : "partner_id"}

    def onchange_address(self, cr, uid, ids, use_parent_address, parent_id, context=None):
        return self.pool.get("res.partner").onchange_address(cr, uid, ids, use_parent_address, parent_id, context=context)

    def onchange_state(self, cr, uid, ids, state_id, context=None):
        return self.pool.get("res.partner").onchange_state(cr, uid, ids, state_id, context=context)

    def on_change_zip(self, cr, uid, ids, zip_code, city):
        return self.pool.get("res.partner").on_change_zip(cr, uid, ids, zip_code, city)

    _columns = {
        "partner_id" : fields.many2one("res.partner", "Partner", required=True, ondelete="cascade"),
        "education_ids" : fields.one2many("eagency.client.education", "client_id", "Education"),
        "skill_ids" : fields.many2many("eagency.skill", "eagency_client_skill_rel", "client_id", "skill_id", "Skills", domain=[("parent_id", "!=", None)]),
        "add_education" : fields.text("Additional Education"),
        "employer_id" : fields.many2one("res.partner", "Employer"),
        "prof_status_id" : fields.many2one("eagency.prof.status", "Professional status"),
        "lang_skill_ids" : fields.one2many("eagency.lang.skill", "client_id", "Language skills"),
        "lang_other" : fields.text("Other language skills"),
        "req_area_ids" : fields.many2many("eagency.area", "eagency_client_area_rel", "client_id", "area_id", "Areas", required=True),
        "req_other" : fields.text("Other mediation requirements"),
        "motivation" : fields.text("Motivation, important conditions and other"),
    }


class eagency_client_education(osv.Model):

    _name = "eagency.client.education"

    _rec_name = "education_id"

    _columns = {
        "client_id" : fields.many2one("eagency.client", "Client", invisible=True, required=True, ondelete="cascade"),
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

    _name = "eagency.skill"

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

    _rec_name = "complete_name"

    _columns = {
        "complete_name" : fields.function(_name_get_fnc, method=True, type="char", size=256, string="Name", select=True),
        "name" : fields.char("Name", size=64, required=True, translate=True),
        "parent_id" : fields.many2one("eagency.skill", "Parent"),
    }

class eagency_prof_status(osv.Model):

    _name = "eagency.prof.status"

    _columns = {
        "name" : fields.char("Name", required=True, size=64, translate=True)
    }


class eagency_area(osv.Model):

    _name = "eagency.area"

    _columns = {
        "name" : fields.char("Name", required=True, size=64, translate=True),
        "country_ids" : fields.many2many("res.country", "eagency_area_country_rel", "area_id", "country_id", "Countries"),
    }


class eagency_lang(osv.Model):

    _name = "eagency.lang"

    _columns = {
        "name" : fields.char("Name", required=True, size=64, translate=True),
        "code" : fields.char("Code", required=True, size=8),
    }


class eagency_lang_skill(osv.Model):

    _name = "eagency.lang.skill"
    _rec_name = "language_id"

    _columns = {
        "language_id" : fields.many2one("eagency.lang", "Language", required=True),
        "skill" : fields.selection([("none", "None / Few"), ("intermediate", "Intermediate"),
                                    ("fluent", "Fluent"), ("mother_language", "Mother language")], "Language skill", required=True),
        "client_id" : fields.many2one("eagency.client", "Client", invisible=True,  required=True, ondelete="cascade")
    }

