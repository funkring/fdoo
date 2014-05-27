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
from openerp.osv import osv
import time


class account_analytic_line(osv.Model):

    def invoice_cost_create(self, cr, uid, ids, data=None, context=None):
        analytic_account_obj = self.pool.get('account.analytic.account')
        account_payment_term_obj = self.pool.get('account.payment.term')
        invoice_obj = self.pool.get('account.invoice')
        product_obj = self.pool.get('product.product')
        invoice_factor_obj = self.pool.get('hr_timesheet_invoice.factor')
        fiscal_pos_obj = self.pool.get('account.fiscal.position')
        product_uom_obj = self.pool.get('product.uom')
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoices = []
        if context is None:
            context = {}
        if data is None:
            data = {}

        journal_types = {}
        f = format.LangFormat(cr, uid, context)

        # prepare for iteration on journal and accounts
        for line in self.pool.get('account.analytic.line').browse(cr, uid, ids, context=context):
            if line.journal_id.type not in journal_types:
                journal_types[line.journal_id.type] = set()
            journal_types[line.journal_id.type].add(line.account_id.id)
        for journal_type, account_ids in journal_types.items():
            for account in analytic_account_obj.browse(cr, uid, list(account_ids), context=context):
                partner = account.partner_id
                if (not partner) or not (account.pricelist_id):
                    raise osv.except_osv(_('Analytic Account Incomplete!'),
                            _('Contract incomplete. Please fill in the Customer and Pricelist fields.'))

                date_due = False
                if partner.property_payment_term:
                    pterm_list= account_payment_term_obj.compute(cr, uid,
                            partner.property_payment_term.id, value=1,
                            date_ref=time.strftime('%Y-%m-%d'))
                    if pterm_list:
                        pterm_list = [line[0] for line in pterm_list]
                        pterm_list.sort()
                        date_due = pterm_list[-1]

                cr.execute("SELECT MIN(line.date), MAX(line.date) " \
                        "FROM account_analytic_line as line " \
                        "WHERE account_id = %s " \
                            "AND id IN %s AND to_invoice IS NOT NULL", (account.id, tuple(context["active_ids"]),))
                                                              
                for row in cr.fetchall():
                    invoice_name = "%s %s - %s" % ( account.name or "",f.formatLang(row[0],date=True), f.formatLang(row[1],date=True))
            
                if not invoice_name:
                    invoice_name = "%s %s" % (account.name or "",f.formatLang(util.currentDate(),date=True)) 

                curr_invoice = {
                    'name': invoice_name,
                    'partner_id': account.partner_id.id,
                    'company_id': account.company_id.id,
                    'payment_term': partner.property_payment_term.id or False,
                    'account_id': partner.property_account_receivable.id,
                    'currency_id': account.pricelist_id.currency_id.id,
                    'date_due': date_due,
                    'fiscal_position': account.partner_id.property_account_position.id
                }
                context2 = context.copy()
                context2['lang'] = partner.lang
                # set company_id in context, so the correct default journal will be selected
                context2['force_company'] = curr_invoice['company_id']
                # set force_company in context so the correct product properties are selected (eg. income account)
                context2['company_id'] = curr_invoice['company_id']

                last_invoice = invoice_obj.create(cr, uid, curr_invoice, context=context2)
                invoices.append(last_invoice)

                cr.execute("""SELECT product_id, user_id, to_invoice, sum(amount), sum(unit_amount), product_uom_id
                        FROM account_analytic_line as line LEFT JOIN account_analytic_journal journal ON (line.journal_id = journal.id)
                        WHERE account_id = %s
                            AND line.id IN %s AND journal.type = %s AND to_invoice IS NOT NULL
                        GROUP BY product_id, user_id, to_invoice, product_uom_id""", (account.id, tuple(ids), journal_type))

                for product_id, user_id, factor_id, total_price, qty, uom in cr.fetchall():
                    context2.update({'uom': uom})

                    if data.get('product'):
                        # force product, use its public price
                        product_id = data['product'][0]
                        unit_price = self._get_invoice_price(cr, uid, account, product_id, user_id, qty, context2)
                    elif journal_type == 'general' and product_id:
                        # timesheets, use sale price
                        unit_price = self._get_invoice_price(cr, uid, account, product_id, user_id, qty, context2)
                    else:
                        # expenses, using price from amount field
                        unit_price = total_price*-1.0 / qty

                    factor = invoice_factor_obj.browse(cr, uid, factor_id, context=context2)
                    # factor_name = factor.customer_name and line_name + ' - ' + factor.customer_name or line_name
                    factor_name = factor.customer_name
                    curr_line = {
                        'price_unit': unit_price,
                        'quantity': qty,
                        'product_id': product_id or False,
                        'discount': factor.factor,
                        'invoice_id': last_invoice,
                        'name': factor_name,
                        'uos_id': uom,
                        'account_analytic_id': account.id,
                    }
                    product = product_obj.browse(cr, uid, product_id, context=context2)
                    if product:
                        factor_name = product_obj.name_get(cr, uid, [product_id], context=context2)[0][1]
                        if factor.customer_name:
                            factor_name += ' - ' + factor.customer_name

                        general_account = product.property_account_income or product.categ_id.property_account_income_categ
                        if not general_account:
                            raise osv.except_osv(_("Configuration Error!"), _("Please define income account for product '%s'.") % product.name)
                        taxes = product.taxes_id or general_account.tax_ids
                        tax = fiscal_pos_obj.map_tax(cr, uid, account.partner_id.property_account_position, taxes)
                        curr_line.update({
                            'invoice_line_tax_id': [(6,0,tax )],
                            'name': factor_name,
                            'invoice_line_tax_id': [(6,0,tax)],
                            'account_id': general_account.id,
                        })
                    #
                    # Compute for lines
                    #
                    cr.execute("SELECT * FROM account_analytic_line WHERE account_id = %s and id IN %s AND product_id=%s and to_invoice=%s ORDER BY account_analytic_line.date", (account.id, tuple(ids), product_id, factor_id))

                    line_ids = cr.dictfetchall()
                    note = []
                    for line in line_ids:
                        # set invoice_line_note
                        details = []
                        #blocks = 0
                        if data.get('date', False):
                            #blocks+=1
                            details.append(f.formatLang(line['date'],date=True))                           
                        if data.get('time', False):
                            #blocks+=1                            
                            if line['product_uom_id']:
                                details.append("%s %s" % (f.formatLang(line['unit_amount']), product_uom_obj.browse(cr, uid, [line['product_uom_id']],context2)[0].name))
                            else:
                                details.append("%s" % (f.formatLang(line['unit_amount']), ))
                        # within name
                        if data.get('name', False):  #and blocks <= 1:
                            details.append(line['name'])
                        note.append(u' - '.join(map(lambda x: unicode(x) or '',details)))
                        # after name
                        #if data.get('name', False) and blocks > 1:
                        #    note.append(line['name'])
                        #    note.append("")
                    if note:
                        curr_line['name'] += "\n" + ("\n".join(map(lambda x: unicode(x) or '',note)))
                    invoice_line_obj.create(cr, uid, curr_line, context=context)
                    cr.execute("update account_analytic_line set invoice_id=%s WHERE account_id = %s and id IN %s", (last_invoice, account.id, tuple(ids)))

                invoice_obj.button_reset_taxes(cr, uid, [last_invoice], context)
        return invoices

    
    _inherit = "account.analytic.line"
