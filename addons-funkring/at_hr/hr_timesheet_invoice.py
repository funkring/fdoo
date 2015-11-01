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

from openerp.addons.at_base import util
from openerp.addons.at_base import format
from openerp.tools.translate import _
from openerp.osv import osv
import time


class account_analytic_line(osv.Model):

    def _prepare_cost_invoice(self, cr, uid, partner, company_id, currency_id, analytic_lines, context=None):
        res = super(account_analytic_line, self)._prepare_cost_invoice(cr, uid, partner, company_id, currency_id, analytic_lines, context=context)
        
        line_ids = [l.id for l in analytic_lines]
        account = analytic_lines[0].account_id
        f = format.LangFormat(cr, uid, context)
         
        cr.execute("SELECT MIN(line.date), MAX(line.date) " \
                    "FROM account_analytic_line as line " \
                    "WHERE account_id = %s " \
                        "AND id IN %s AND to_invoice IS NOT NULL", (account.id, tuple(line_ids)))

        invoice_name = None
        for date_from, date_to in cr.fetchall():
            if date_from and date_to:
                invoice_name = "%s %s - %s" % ( account.name or "",f.formatLang(date_from,date=True), f.formatLang(date_to,date=True))

        if not invoice_name:
            invoice_name = "%s %s" % (account.name or "",f.formatLang(util.currentDate(),date=True))

        res["name"] = invoice_name
        return res
    
    def _prepare_cost_invoice_line(self, cr, uid, invoice_id, product_id, uom, user_id,
                factor_id, account, analytic_lines, journal_type, data, context=None):
        product_obj = self.pool['product.product']
        
        f = format.LangFormat(cr, uid, context)
        uom_context = dict(context or {}, uom=uom)
         
        total_price = sum(l.amount for l in analytic_lines)
        total_qty = sum(l.unit_amount for l in analytic_lines)

        if data.get('product'):
            # force product, use its public price
            if isinstance(data['product'], (tuple, list)):
                product_id = data['product'][0]
            else:
                product_id = data['product']
            unit_price = self._get_invoice_price(cr, uid, account, product_id, user_id, total_qty, uom_context)
        elif journal_type == 'general' and product_id:
            # timesheets, use sale price
            unit_price = self._get_invoice_price(cr, uid, account, product_id, user_id, total_qty, uom_context)
        else:
            # expenses, using price from amount field
            unit_price = total_price*-1.0 / total_qty

        factor = self.pool['hr_timesheet_invoice.factor'].browse(cr, uid, factor_id, context=uom_context)
        factor_name = factor.customer_name or ''
        curr_invoice_line = {
            'price_unit': unit_price,
            'quantity': total_qty,
            'product_id': product_id,
            'discount': factor.factor,
            'invoice_id': invoice_id,
            'name': factor_name,
            'uos_id': uom,
            'account_analytic_id': account.id,
        }

        if product_id:
            product = product_obj.browse(cr, uid, product_id, context=uom_context)
            factor_name = product_obj.name_get(cr, uid, [product_id], context=uom_context)[0][1]
            if factor.customer_name:
                factor_name += ' - ' + factor.customer_name

                general_account = product.property_account_income or product.categ_id.property_account_income_categ
                if not general_account:
                    raise osv.except_osv(_('Error!'), _("Configuration Error!") + '\n' + _("Please define income account for product '%s'.") % product.name)
                taxes = product.taxes_id or general_account.tax_ids
                tax = self.pool['account.fiscal.position'].map_tax(cr, uid, account.partner_id.property_account_position, taxes)
                curr_invoice_line.update({
                    'invoice_line_tax_id': [(6, 0, tax)],
                    'name': factor_name,
                    'invoice_line_tax_id': [(6, 0, tax)],
                    'account_id': general_account.id,
                })

            note = []
            for line in analytic_lines:
                # set invoice_line_note
                details = []
                if data.get('date', False):
                    details.append(f.formatLang(line['date'],date=True))
                if data.get('time', False):
                    line_time = f.formatLang(line.unit_amount,float_time=True)
                    if line['product_uom_id']:
                        details.append("%s %s" % (line_time, line.product_uom_id.name))
                    else:
                        details.append("%s" % (line_time, ))
                if data.get('name', False):
                    details.append(line['name'])
                if details:
                    note.append(u' - '.join(map(lambda x: unicode(x) or '', details)))
            if note:
                curr_invoice_line['name'] += "\n" + ("\n".join(map(lambda x: unicode(x) or '', note)))
        return curr_invoice_line
    
        
    _inherit = "account.analytic.line"
