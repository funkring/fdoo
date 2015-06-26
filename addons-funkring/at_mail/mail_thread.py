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


class mail_thread(osv.Model):
    
    def message_duplicate(self, cr, uid, message_id, new_res_id, new_model, context=None):
        """
        duplicate a message

        :param message_id : the message_id 
        :param new_res_id : the new res_id of the mail.message
        :param new_model : the name of the new model of the mail.message

        """
        
        message_obj = self.pool["mail.message"]
        origin_parent = message_obj.read(cr, uid, message_id, ["parent_id"],  context=context)["parent_id"]
        parent_id = None
        if origin_parent:
            parent_id = message_obj.search_id(cr, uid, [("origin_id","=",origin_parent[0])])
        
        return message_obj.copy(cr, uid, message_id, { "parent_id" : parent_id,
                                                       "model" : new_model,
                                                       "res_id" :new_res_id },
                                                        context=context ) 
        
    
    
    _inherit = "mail.thread"
