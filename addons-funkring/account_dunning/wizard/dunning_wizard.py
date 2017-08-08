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
        profile_line_obj = self.pool.get("account.dunning_profile_line")
        profile_obj = self.pool.get("account.dunning_profile")
        partner_obj = self.pool.get("res.partner")
        reminder_line_obj = self.pool.get("account.reminder.line")
        user = self.pool.get("res.users").browse(cr, uid, uid)

        # get profiles for shop
        profiles = profile_obj.browse(cr, uid, profile_obj.search(cr, uid, []), context=context)
        all_shops = set([s.id for s in profiles.mapped('shop_ids')])

        for wizard in self.browse(cr, uid, ids):
            cr.execute("SELECT inv.partner_id FROM account_invoice inv WHERE inv.state='open' "
                        " UNION "
                        " SELECT r.partner_id FROM account_reminder r")

            partner_ids = [r[0] for r in cr.fetchall()]
            reminder_ids = []
                        
            # check if there any partner ids
            if not partner_ids:
                break
            
            # shop id  
            shop_ids = set()    
            if wizard.profile_id.shop_ids:
                for shop in wizard.profile_id.shop_ids:
                    shop_ids.add(shop.id)

            customers = partner_obj.browse(cr,uid,partner_ids,context=context)
            for customer in customers:
                # get active reminder id
                reminder_id = reminder_obj.search_id(cr, uid, [("partner_id", "=", customer.id),("profile_id","=",wizard.profile_id.id)])
                if not customer.noremind:           
                    commercial_partner = customer.commercial_partner_id
                    # check balance      
                    # not commercial_partner.credit (should never happen, but it happens) 
                    if not commercial_partner.credit or commercial_partner.credit > commercial_partner.debit or reminder_id:
                        
                        # check invoice
                        invoice_ids = invoice_obj.search(cr, uid, [("partner_id", "=", customer.id), ("type", "=", "out_invoice"), ("noremind","=",False)])
                        if not invoice_ids:
                            continue

                        lines = []
                        max_profile_line = None
                        profile_line = None

                        # check invoices
                        for inv in invoice_obj.browse(cr, uid, invoice_ids):
                            # check if shop specific reminder defined
                            if all_shops:
                                inv_shop_id = inv.shop_id and inv.shop_id.id or 0
                                # check profile is a general reminder
                                # or continue if not
                                if not shop_ids and inv_shop_id in all_shops:
                                    continue
                                # check if it is a shop specific reminder
                                # or continue if not
                                if shop_ids and not inv_shop_id in shop_ids:
                                    continue
                                                 
                            if (user.company_id == inv.company_id) and inv.payment_term and not inv.noremind:
                                reminder_line_id = reminder_line_obj.search_id(cr, uid, [("reminder_id","=",reminder_id),("invoice_id", "=", inv.id)])
                                if inv.state == "open":
                                    profile_line = profile_line_obj.line_next(cr,uid,wizard.profile_id,inv.profile_line_id,wizard.date,inv.date_due)

                                    # check if no dunning option
                                    if profile_line and profile_line.payment_no_dunning and inv.residual > 0 and inv.residual < inv.amount_total:
                                        profile_line = None

                                    invoice_obj.write(cr,uid,inv.id,{"profile_line_id" : profile_line and profile_line.id or None,
                                                                     "dunning_date" : wizard.date }, context)

                                    # check next remind
                                    if profile_line and inv.residual:                                        
                                        line_values =  {"invoice_id" : inv.id,
                                                        "profile_line_id" : profile_line and profile_line.id or None,
                                                        "amount" : inv.residual}

                                        # update remind
                                        if not reminder_line_id:
                                            lines.append((0, 0, line_values))
                                        else:
                                            lines.append((1, reminder_line_id, line_values))

                                        # determine max profile
                                        if max_profile_line:
                                            if max_profile_line.sequence < profile_line.sequence:
                                                max_profile_line = profile_line
                                        else:
                                            max_profile_line = profile_line

                        #update or create reminder
                        if max_profile_line:
                            values = {"date" : wizard.date,
                                      "partner_id" : customer.id,
                                      "profile_id" : wizard.profile_id.id,
                                      "max_profile_line_id" : max_profile_line.id,
                                      "line_ids" : lines,
                                      "state" : "validated"}
                            
                            # create or update reminder
                            if reminder_id:
                                reminder_obj.write(cr, uid, reminder_id, values, context)
                            else:
                                reminder_id = reminder_obj.create(cr, uid, values, context)
                                
                            # update lines
                            reminder_line_ids = []
                            for line in lines:
                                values = line[2]
                                values["reminder_id"] = reminder_id
                                line_id = line[1]                                
                                if not line_id:                                    
                                    line_id = reminder_line_obj.create(cr, uid, values, context)
                                else:
                                    reminder_line_obj.write(cr, uid, line_id, values, context)
                                # add line
                                reminder_line_ids.append(line_id)
                                
                            # only add if there are lines 
                            if reminder_line_ids:
                                # delete unused lines
                                unused_line_ids = reminder_line_obj.search(cr, uid, [("reminder_id","=",reminder_id),("id","not in",reminder_line_ids)], context=context)
                                reminder_line_obj.unlink(cr, uid, unused_line_ids, context=context)                                
                                # add reminder
                                reminder_ids.append(reminder_id)
                            
            # remove untouched, unused
            unused_reminder_ids = reminder_obj.search(cr, uid, [("id", "not in", reminder_ids),("profile_id","=",wizard.profile_id.id)])
            reminder_obj.unlink(cr, uid, unused_reminder_ids, context=context)
            
        return {
            "name" : _("Reminders"),
            "res_model" : "account.reminder",
            "type" : "ir.actions.act_window",
            "view_type" : "form",
            "view_mode" : "tree,form",
            "clear_breadcrumbs" : True
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
        "date" : lambda *a: util.currentDate(),
        "profile_id" : _default_profile_id
    }

