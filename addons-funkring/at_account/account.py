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

from openerp.osv import osv, fields
from openerp.tools.translate import _

from openerp import api

class account_fiscal_position(osv.osv):
    
    def unmap_tax(self, cr, uid, fposition, mapped_taxes, context=None):
        if not mapped_taxes:
            return []
        if not fposition:
            return map(lambda x: x.id, mapped_taxes)
        result = []
        for mapped_tax in mapped_taxes:
            unmapped = None
            for tax in fposition.tax_ids:
                tax_dest = tax.tax_dest_id
                if tax_dest and tax_dest.id == mapped_tax.id:
                    if unmapped:
                        raise osv.except_osv( _("Error"), _("Cannot do reverse mapping of Tax %s because or than one tax match") % (tax_dest.name,) )
                    unmapped = tax.tax_src_id       
            if not unmapped:
                raise osv.except_osv( _("Error"), _("Cannot do reverse mapping of Tax %s because no one match") % (tax_dest.name,) )
            result.append(unmapped)
        return result
    
    _inherit = 'account.fiscal.position'


class account_account(osv.osv):
    
    def _compute_account(self,cr,uid,ids,date_till=None,context=None):
        query = []
        query_params = []
        if date_till:
            query.append("l.date <= '%s'" % (date_till,) )
        
        query_str = " AND ".join(query)        
        return self.__compute(cr,uid,ids,field_names=["credit","debit","balance"], arg=None, context=context, query=query_str , query_params=tuple(query_params))
    
    _inherit = "account.account"


class account_period(osv.osv):
    
    def find_period_id(self, cr, uid, dt, context=None):
        if dt:
            args = [('date_start','<=',dt),('date_stop','>=',dt)]
            
            # add company
            if context.get('company_id', False):
                args.append(('company_id', '=', context['company_id']))
            else:
                company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
                args.append(('company_id', '=', company_id))
                
            ids = self.search(cr, uid, args, limit=1, context=context)
            if ids:
                return ids[0]
        return None
    
    _inherit = "account.period"


class account_invoice(osv.osv):
    
    def _cancel_invoice_all(self, cr, uid, invoice, context=None):
        if invoice.state in ("cancel","draft"):
            return False
        
        voucher_obj = self.pool["account.voucher"]
        move_obj = self.pool["account.move"]
        invoice_obj = self.pool["account.invoice"]
        
        move_ids = set()
        voucher_ids = []
        
        for move_line in invoice.payment_ids:
            move_ids.add(move_line.move_id.id)
        
        # cancel moves and get vouchers
        move_ids = list(move_ids)
        for move_id in move_ids:
            voucher_ids.extend(voucher_obj.search(cr, uid, [("move_id","=",move_id)]))
        move_obj.button_cancel(cr, uid, move_ids, context=context)
            
        # cancel and delete voucher
        voucher_obj.cancel_voucher(cr, uid, voucher_ids, context=context)
        voucher_obj.unlink(cr, uid, voucher_ids, context=context)         
        # cancel invoice
        invoice_obj.action_cancel(cr, uid, [invoice.id], context=context)
        return True
    
    _inherit = "account.invoice"
    

class account_journal(osv.osv):
    
    def name_get(self, cr, user, ids, context=None):
        """
        Returns a list of tupples containing id, name.
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param ids: list of ids for which name should be read
        @param context: context arguments, like lang, time zone

        @return: Returns a list of tupples containing id, name
        """
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.browse(cr, user, ids, context=context)
        res = []
        for rs in result:
            if rs.currency:
                currency = rs.currency
            else:
                currency = rs.company_id.currency_id
                
            company_code = rs.company_id.code
            if company_code:
                name = "%s %s (%s)" % (rs.name, company_code, currency.name)
            else:
                name = "%s (%s)" % (rs.name, currency.name)
                
            res += [(rs.id, name)]
        return res
    
    _inherit = "account.journal"
    
    
class account_tax(osv.osv):
    
    _inherit = "account.tax"
    
    @api.v7
    def compute_full(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None, force_excluded=False, force_included=False, netto_to_price=False):
        """
        :param force_excluded: boolean used to say that we don't want to consider the value of field price_include of
            tax. It's used in encoding by line where you don't matter if you encoded a tax with that boolean to True or
            False.
            If list_price is True the price_unit is netto and the list_price was calculated. 
            If force_included is True the price_unit is a brutto price. 
        RETURN: {
                'total': 0.0,                # Total without taxes
                'total_included: 0.0,        # Total with taxes
                'taxes': []                  # List of taxes, see compute for the format
            }
        """

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        tax_compute_precision = precision
        if taxes and taxes[0].company_id.tax_calculation_rounding_method == 'round_globally':
            tax_compute_precision += 5
        totalin = totalex = round(price_unit * quantity, precision)
        tin = []
        tex = []
        for tax in taxes:
            # funkring.net - begin
            if netto_to_price:
                if tax.price_include:
                    tex.append(tax)
            else:
                if not force_included and (not tax.price_include or force_excluded):
                    tex.append(tax)
                else:
                    tin.append(tax)
            # funkring.net - end
        tin = self.compute_inv(cr, uid, tin, price_unit, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tin:
            totalex -= r.get('amount', 0.0)
        totlex_qty = 0.0
        try:
            totlex_qty = totalex/quantity
        except:
            pass
        tex = self._compute(cr, uid, tex, totlex_qty, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tex:
            totalin += r.get('amount', 0.0)
        return {
            'total': totalex,
            'total_included': totalin,
            'taxes': tin + tex
        }

    @api.v8
    def compute_full(self, price_unit, quantity, product=None, partner=None, force_excluded=False, force_included=False, netto_to_price=False):
        return account_tax.compute_all(
            self._model, self._cr, self._uid, self, price_unit, quantity,
            product=product, partner=partner, force_excluded=force_excluded, force_included=force_included, netto_to_price=netto_to_price)
    
