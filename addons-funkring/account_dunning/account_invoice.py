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

class account_invoice(osv.osv):
    
    def copy(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}        
        if not default.has_key("profile_line_id"):        
            default["profile_line_id"]=None
        if not default.has_key("dunning_date"):        
            default["dunning_date"]=None
        copy_id =  super(account_invoice,self).copy(cr,uid,oid,default,context)
        return copy_id        

    def _get_followup_line(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids)
        reminder_line_obj = self.pool.get("account.reminder.line")
        
        for invoice in self.browse(cr, uid, ids, context):
            reminder_line_ids = reminder_line_obj.search(cr, uid, [("invoice_id", "=", invoice.id)])
            if reminder_line_ids:
                reminder_line = reminder_line_obj.browse(cr, uid, reminder_line_ids[0], context)
                res[invoice.id] = reminder_line.profile_line_id.id
                
        return res
    
    _inherit = "account.invoice"
    _columns = {
        "profile_line_id" : fields.function(_get_followup_line, type="many2one", obj="account.dunning_profile_line", method=True, string="Dunning level"),
        "dunning_date" : fields.date("Dunning date"),
        "noremind" : fields.boolean("No Remind",
                                    help="If 'No Remind' is true, then the customer won't get remind for the actual invoice!")
    }