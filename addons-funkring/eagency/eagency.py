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

class eagency_client(osv.Model):

    def onchange_address(self, cr, uid, ids, use_parent_address, parent_id, context=None):
        return self.pool.get("res.partner").onchange_address(cr, uid, ids, use_parent_address, parent_id, context=context)

    def onchange_state(self, cr, uid, ids, state_id, context=None):
        return self.pool.get("res.partner").onchange_state(cr, uid, ids, state_id, context=context)

    def on_change_zip(self, cr, uid, ids, zip_code, city):
        return self.pool.get("res.partner").on_change_zip(cr, uid, ids, zip_code, city)

    def _user_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT c.id, u.id FROM eagency_client c " 
                   " INNER JOIN res_partner p ON p.id = c.partner_id "
                   " INNER JOIN res_users u ON u.partner_id = p.id "
                   " WHERE c.id IN %s " 
                   " GROUP BY 1,2", (tuple(ids),))
        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res
    
    def _user_active(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT c.id, u.active FROM eagency_client c " 
                   " INNER JOIN res_partner p ON p.id = c.partner_id "
                   " INNER JOIN res_users u ON u.partner_id = p.id "
                   " WHERE c.id IN %s " 
                   " GROUP BY 1,2", (tuple(ids),))
        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res
        
    def _relids_user_ids(self, cr, uid, ids, context=None):
        cr.execute("SELECT c.id FROM res_users u " 
                   " INNER JOIN res_partner p ON p.id = u.partner_id "
                   " INNER JOIN eagency_client c ON c.partner_id = p.id "
                   " WHERE u.id IN %s " 
                   " GROUP BY 1", (tuple(ids),))
        return [r[0] for r in cr.fetchall()]
    
    def _send_mails(self, cr, uid, template_xmlid, ids, context=None):
        template_obj = self.pool["email.template"]
        template_id = self.pool["ir.model.data"].xmlid_to_res_id(cr, uid, template_xmlid)
        if template_id:
            for client in self.browse(cr, uid, ids, context=context):
                template_obj.send_mail(cr, uid, template_id, client.id, force_send=True, context=context)

    
    def unlink(self, cr, uid, ids, context):
        ids = util.idList(ids)     
        user_ids = []
        for client in self.browse(cr, uid, ids, context=context):
            if client.user_id:   
                user_ids.append(client.user_id.id)             
                
        super(eagency_client,self).unlink(cr, uid, ids, context=context)
        
        user_obj = self.pool["res.users"]
        if user_ids:
            user_obj.unlink(cr, uid, user_ids, context=context)             
        


    _name = "eagency.client"
    _inherits = {"res.partner" : "partner_id"}
    _columns = {
        "title_name" : fields.char("Title"),
        "partner_id" : fields.many2one("res.partner", "Partner", required=True, ondelete="cascade"),
        "education_ids" : fields.one2many("eagency.client.education", "client_id", "Education"),
        "skill_ids" : fields.many2many("eagency.skill", "eagency_client_skill_rel", "client_id", "skill_id", "Skills"),
        "add_education" : fields.text("Additional Education"),     
        "employer_id" : fields.many2one("res.partner", "(Registered) Employer"),
        "prof_status_id" : fields.many2one("eagency.prof.status", "(Registered) Professional status"),
        "lang_skill_ids" : fields.one2many("eagency.lang.skill", "client_id", "Language skills"),
        "lang_other" : fields.text("Other language skills"),
        "req_area_ids" : fields.many2many("eagency.area", "eagency_client_area_rel", "client_id", "area_id", "Areas", required=True),
        "req_other" : fields.text("Other mediation requirements"),
        "motivation" : fields.text("Motivation, important conditions and other"),
        "user_id" : fields.function(_user_id, string="User", type="many2one", obj="res.users", copy=False, store={
            "res.users" : (_relids_user_ids,["partner_id"],10),
            "eagency.client": (lambda self, cr, uid, ids, context=None: ids, ["partner_id"],10)
        }),
        "activated" : fields.function(_user_active, string="Activated", type="boolean", copy=False, store={
            "res.users" : (_relids_user_ids,["partner_id"],10),
            "eagency.client": (lambda self, cr, uid, ids, context=None: ids, ["partner_id"],10)
        }),
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
                                    ("fluent", "Fluent"), ("mother_language", "Mother language")], "Language skill", required=True),
        "client_id" : fields.many2one("eagency.client", "Client", invisible=True,  required=True, ondelete="cascade")
    }

