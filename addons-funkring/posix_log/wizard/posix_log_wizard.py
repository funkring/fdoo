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
from openerp.tools.translate import _

class posix_log_wizard(osv.Model):
    _name = "posix.log.wizard"
    _description = "Posix log wizard"
    
    def do_verify(self, cr, uid, ids, context=None):
        thread_obj = self.pool.get("mail.thread")
        log_obj = self.pool.get("posix.log")
        log_id = context.get("active_id")
        
        for wizard in self.browse(cr, uid, ids):
            context["thread_model"] = "posix.log"
            thread_id = thread_obj.message_post(cr, uid, log_id, subject=_("Confirmation"),body=wizard.note, context=context)
            if context.get("active_model") == "posix.log":
                log_obj.write(cr, uid, log_id, {"confirm_id" : thread_id})
            else:
                raise osv.except_osv( _("Error"), _("The active model is not posix.log"))
        return {
            "type" : "ir.actions.client",
            "tag" : "reload"
        }
                
        
    _columns = {
        "note" : fields.text("Note")
    }