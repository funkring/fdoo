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
from openerp.addons.at_base import util
from openerp.tools.translate import _

class account_dunning_wizard(osv.osv_memory):
    
    def create_reminders(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get("account.invoice")
        reminder_obj = self.pool.get("account.reminder")
        profile_line_obj=self.pool.get("account.dunning_profile_line")
        partner_obj = self.pool.get("res.partner")
        reminder_line_obj = self.pool.get("account.reminder.line")
        user = self.pool.get("res.users").browse(cr, uid, uid)
        
        for wizard in self.browse(cr, uid, ids):
            cr.execute("SELECT inv.partner_id FROM account_invoice inv WHERE inv.state='open' "
                        " UNION "
                        " SELECT r.partner_id FROM account_reminder r")
            
            partner_ids = [r[0] for r in cr.fetchall()]
            if not partner_ids:
                break
            
            customers = partner_obj.browse(cr,uid,partner_ids,context=context)
            for customer in customers:
                if not customer.noremind:
                    reminder_id = reminder_obj.search_id(cr, uid, [("partner_id", "=", customer.id),("profile_id","=",wizard.profile_id.id)])
                    customer_balance_check = customer
                    if customer.parent_id:
                        customer_balance_check = customer.parent_id
                        
                    if customer_balance_check.credit <= customer_balance_check.debit and not reminder_id:
                            continue
                    else:
                        invoice_ids = invoice_obj.search(cr, uid, [("partner_id", "=", customer.id), ("type", "=", "out_invoice"), ("noremind","=",False)])
                        if not invoice_ids:
                            continue
                        
                        lines = []
                        max_profile_line = None
                        profile_line = None
                        
                        for inv in invoice_obj.browse(cr, uid, invoice_ids):
                            if (user.company_id == inv.company_id) and inv.payment_term and not inv.noremind:
                                reminder_line_id = reminder_line_obj.search_id(cr, uid, [("reminder_id","=",reminder_id),("invoice_id", "=", inv.id)])
                                if reminder_line_id and inv.state in ["paid", "cancel"] :
                                    lines.append((2, reminder_line_id))
                                
                                elif inv.state == "open":
                                    profile_line = profile_line_obj.line_next(cr,uid,wizard.profile_id,inv.profile_line_id,wizard.date,inv.date_due)
                                    invoice_obj.write(cr,uid,inv.id,{"profile_line_id" : profile_line and profile_line.id or None,
                                                                     "dunning_date" : wizard.date }, context)
                                    
                                    # check next remind
                                    if not profile_line:
                                        if reminder_line_id:
                                            lines.append((2, reminder_line_id))
                                        else:
                                            continue
                                    
                                    else:
                                        line_values =  {"invoice_id" : inv.id,
                                                        "profile_line_id" : profile_line and profile_line.id or None,
                                                        "amount" : inv.residual}
                                        
                                        if not reminder_line_id:
                                            lines.append((0, 0, line_values))
                                        else:
                                            lines.append((1, reminder_line_id, line_values))
                                            
                                        if max_profile_line:
                                            if max_profile_line.sequence < profile_line.sequence:
                                                max_profile_line = profile_line
                                        else:
                                            max_profile_line = profile_line
                        
                        #update or create reminder
                        if lines:
                            values = {"date" : wizard.date,
                                      "partner_id" : customer.id,
                                      "profile_id" : wizard.profile_id.id,
                                      "max_profile_line_id" : max_profile_line and max_profile_line.id or None,
                                      "line_ids" : lines}
                            
                            if reminder_id:
                                reminder_obj.write(cr, uid, reminder_id, values, context)
                                
                            else:
                                reminder_obj.create(cr, uid, values, context)
                        
                        # check if reminder is ready to delete
                        elif reminder_id:
                            reminder_obj.unlink(cr, uid, reminder_id, context)
                                              
        return {
            "name" : _("Reminders"),
            "res_model" : "account.reminder",      
            "type" : "ir.actions.act_window",
            "view_type" : "form",
            "view_mode" : "tree,form"
        }
    
    
    def _default_profile_id(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        return self.pool.get("account.dunning_profile").search_id(cr, uid, [("company_id","=",company_id)], context=context)
        
    
    _name="account.dunning_wizard"
    _columns = {
        "date": fields.date("Reminder date", required=True),
        "profile_id" : fields.many2one("account.dunning_profile", "Profile", required=True),
    }    
    _defaults = {
        "date" : util.currentDate(),
        "profile_id" : _default_profile_id     
    }
    
