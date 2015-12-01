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
from openerp import SUPERUSER_ID

class semester_assistant(osv.TransientModel):
    
    def action_change(self, cr, uid, ids, context=None):
        user_obj = self.pool["res.users"]
        if not user_obj.has_group(cr, uid, "academy.group_management"):
            raise osv.except_osv(_("Error"), _("Only academy manager could change semester!"))
        
        user = user_obj.browse(cr, uid, uid, context=context)
        wizard = self.browse(cr, uid, ids[0], context)
        company_obj = self.pool["res.company"]
        company_obj.write(cr, SUPERUSER_ID, user.company_id.id, {"academy_semester_id" : wizard.semester_id.id }, context=context)
        return {'type': 'ir.actions.act_window_close'}
        
    def _default_semester_id(self, cr, uid, context=None):
        user_obj = self.pool["res.users"]
        user = user_obj.browse(cr, uid, uid, context=context)
        return user.company_id.academy_semester_id.id
        
    _name = "academy.semester.assistant"
    _description = "Semester Configuration"
    _rec_name = "semester_id"
    _columns = {
        "semester_id" : fields.many2one("academy.semester", "Current Semester", required=True, 
                                    help="Switch to the current semester")
    }
    _defaults = {
        "semester_id" : _default_semester_id
    }
        