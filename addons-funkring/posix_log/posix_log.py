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

class posix_log(osv.Model):
    _name = "posix.log"
    _inherit = ["mail.thread"]
    _description = "Posix Log"
    
    def do_quit(self, cr, uid, ids, context=None):
        return {
            "name" : _("Quit Alarm"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "posix.log.wizard",
            "type": "ir.actions.act_window",
            "target" : "new",
            "context": context,
        }
    
    _columns = {
        "name" : fields.char("Name", size=64, readonly=True),
        "priority" : fields.selection([("0", "0 Emergency"), 
                                       ("1", "1 Alert"),
                                       ("2", "2 Critical"), 
                                       ("3", "3 Error"), 
                                       ("4", "4 Warning"),
                                       ("5", "5 Notice"), 
                                       ("6", "6 Informational"), 
                                       ("7", "7 Debug")], "Priority", size=1, readonly=True),
        "facility_id" : fields.many2one("posix.log.facility", "Facility", readonly=True),
        "date" : fields.datetime("Date", readonly=True),
        "source" : fields.char("Source", size=64, readonly=True),
        "message" : fields.text("Message", readonly=True),
        "confirm_id" : fields.many2one("mail.message", "Note", readonly=True),
    }
    

class posix_log_facilty(osv.Model):
    _name = "posix.log.facility"
    _description = "Log facility"
    _columns = {
        "code" : fields.char("Code", size=16, select=True),
        "priority" : fields.selection([("0", "0 Emergency"), 
                                       ("1", "1 Alert"),
                                       ("2", "2 Critical"), 
                                       ("3", "3 Error"), 
                                       ("4", "4 Warning"),
                                       ("5", "5 Notice"), 
                                       ("6", "6 Informational"), 
                                       ("7", "7 Debug")], "Priority", size=1, readonly=True),
        "name" : fields.char("Name", size=64, translateable=True),
        "description" : fields.text("Description"),
    }