# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

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

from openerp.osv import fields,osv

class account_reminder(osv.Model):
    
    def action_reminder_send(self, cr, uid, ids, context=None):
        """
        This function opens a window to compose an email, with the edi reminder template message loaded by default
        """
        assert len(ids) == 1, "This option should only be used for a single id at a time."
        ir_model_data = self.pool.get("ir.model.data")
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, "account_dunning", "email_template_edi_reminder")[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, "mail", "email_compose_message_wizard_form")[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        ctx.update({
            "default_model": "account.reminder",
            "default_res_id": ids[0],
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment"
        })
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": ctx,
        }
    
    _name="account.reminder"
    _inherit = ["mail.thread"]
    _rec_name="date"
    _columns = {
        "date" : fields.date("Date", required=True),
        "partner_id" : fields.many2one("res.partner", "Partner", required=True),
        "profile_id" : fields.many2one("account.dunning_profile", "Profile", required=True),
        "max_profile_line_id" : fields.many2one("account.dunning_profile_line", "Highest dunning level"),
        "line_ids" : fields.one2many("account.reminder.line", "reminder_id", string="Lines")
    }
    

class account_reminder_line(osv.Model):
    
    def unlink(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get("account.invoice")
        
        for line in self.browse(cr, uid, ids, context):
            invoice_obj.write(cr, uid, [line.invoice_id.id], {"followup_line_id" : None,
                                                              "followup_date" : None})
            
        return super(account_reminder_line, self).unlink(cr, uid, ids, context=context)
    
    def onchange_invoice(self, cr, uid, ids, invoice_id):
        res = {
            "value" : {}
        }
        
        amount = 0.0
        if invoice_id:
            invoice_obj = self.pool.get("account.invoice")
            amount = invoice_obj.browse(cr, uid, invoice_id).residual
        
        res["value"]["amount"] = amount
        
        return res
    
    _name="account.reminder.line"
    _rec_name="invoice_id"
    
    _columns = {
        "reminder_id" : fields.many2one("account.reminder", "Reminder", ondelete="cascade", select=True),
        "invoice_id" : fields.many2one("account.invoice", "Invoice", ondelete="cascade", select=True, required=True),
        "profile_line_id" : fields.many2one("account.dunning_profile_line", "Dunning level", required=True),
        "amount" : fields.float("Residual", readonly=True),
    }
    
