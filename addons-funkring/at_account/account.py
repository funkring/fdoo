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
account_fiscal_position()


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


class account_journal(osv.osv):
    
    _inherit = "account.journal"    
    _columns = {
        "compensation_ids" : fields.one2many("account.bank.statement.compensation","journal_id","Compensations"),
        "ignore_payment_term" : fields.boolean("Ignore Payment Term",
                                                help="If you have made two lines for the payment term, then the system will not create two account move lines for each payment term line.")
    }
