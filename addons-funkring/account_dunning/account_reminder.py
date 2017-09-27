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
from openerp.tools.translate import _
from openerp.exceptions import Warning

class mail_compose_message(osv.TransientModel):

    def send_mail(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get("default_model") == "account.reminder":
            reminder_obj = self.pool["account.reminder"]
            for wizard in self.browse(cr, uid, ids, context=context):
                res_ids = self._res_ids(wizard, context)
                reminder_obj.write(cr, uid, res_ids, {"state" : "sent"}, context=context)
        return super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)

    _inherit = "mail.compose.message"

class account_reminder(osv.Model):

    def send_reminder_mail(self, cr, uid, ids, context=None):
        model_data_obj = self.pool["ir.model.data"]
        template_id = model_data_obj.get_object_reference(cr, uid, "account_dunning", "email_to_customer_reminder")[1]
        compose_form = model_data_obj.get_object_reference(cr, uid, "mail", "email_compose_message_wizard_form")[1]

        if ids and template_id and compose_form:
            composition_mode = len(ids) > 1 and "mass_mail" or "comment"
            
            partner_ids = set()
            profile_template_id = None
            
            for reminder in self.browse(cr, uid, ids, context=context):
                reminder_template = reminder.profile_id.template_id
                if reminder_template:
                    if not profile_template_id:
                        profile_template_id = reminder_template.id
                    elif profile_template_id != reminder_template.id:
                        raise Warning(_("You cannot send mass e-mails with different dunning profiles"))
                    
                partner_ids.add(reminder.partner_id.id)
                if reminder.state == ("sent"):
                    raise Warning(_('The reminder was already sent to the customer. If you want to send a reminder again,'
                                                          'you need to call the reminder wizard again!'))
            if profile_template_id:
                template_id = profile_template_id

            email_context = {
                "active_ids" : ids,
                "active_id" : ids[0],
                "active_model" : "account.reminder",
                "default_model" : "account.reminder",
                "default_res_id" : ids[0],
                "default_composition_mode" : composition_mode,
                "default_template_id" : template_id,
                "default_use_template" : bool(template_id)
            }

            return {
                    "name": _("Compose Email"),
                    "type": "ir.actions.act_window",
                    "view_type": "form",
                    "view_mode": "form",
                    "res_model": "mail.compose.message",
                    "views": [(compose_form, "form")],
                    "view_id": compose_form,
                    "target": "new",
                    "context": email_context,
            }

        return True

    _name="account.reminder"
    _inherit = ["mail.thread"]
    _rec_name="date"
    _columns = {
        "date" : fields.date("Date", required=True),
        "partner_id" : fields.many2one("res.partner", "Partner", required=True),
        "profile_id" : fields.many2one("account.dunning_profile", "Profile", required=True),
        "shop_id" : fields.related("profile_id", "shop_id", type="many2one", obj="sale.shop", string="Shop", readonly=True),
        "max_profile_line_id" : fields.many2one("account.dunning_profile_line", "Highest dunning level"),
        "line_ids" : fields.one2many("account.reminder.line", "reminder_id", string="Lines"),
        "state": fields.selection([('validated', 'Validated'), ('sent', 'Reminder sent'),], "State", readonly=True, copy=False),
    }


class account_reminder_line(osv.Model):

    def unlink(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get("account.invoice")

        for line in self.browse(cr, uid, ids, context):
            invoice_obj.write(cr, uid, [line.invoice_id.id], {"dunning_date" : None})

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

