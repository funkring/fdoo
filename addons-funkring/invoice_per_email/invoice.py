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

from openerp import models, fields, api
from openerp.osv.orm import setup_modifiers
from openerp.tools.safe_eval import expr_eval
from lxml import etree

class account_invoice(models.Model):
    _name = "account.invoice"
    _inherit = "account.invoice"
    
    invoice_per_email = fields.Boolean("Invoice per E-Mail")

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        partner_id = vals.get("partner_id")
        if partner_id and not vals.has_key("invoice_per_email"):
            partner = self.env["res.partner"].browse(partner_id)
            vals["invoice_per_email"] = partner.invoice_per_email            
        return super(account_invoice, self).create(vals)
    
    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
                             payment_term=False, partner_bank_id=False, company_id=False):

       
        res = super(account_invoice, self).onchange_partner_id(type, partner_id, date_invoice=date_invoice, payment_term=payment_term, partner_bank_id=partner_bank_id, company_id=company_id)
        if partner_id:
            
            values = res.get("value",None)
            if values is None:
                res["value"] = values = {}
            
            partner_obj = self.env["res.partner"]
            partner = partner_obj.browse(partner_id)
            values["invoice_per_email"] = partner.invoice_per_email
        
        return res
    
    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        context = self._context

        res = super(account_invoice, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            if context.get('type') in ('out_invoice', 'out_refund'):
                for node in doc.xpath("//field[@name='invoice_per_email']"):
                    node.set('invisible', '0')
                    setup_modifiers(node, context=self._context, in_tree_view=True)#                 

            res['arch'] = etree.tostring(doc)
            
        return res
