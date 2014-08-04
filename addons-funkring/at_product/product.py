#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martinr@funkring.net>
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
import re


class product_uom_categ(osv.osv):
    _inherit = "product.uom.categ"
    _columns = {
       "uom_ids" : fields.one2many("product.uom","category_id","Grouped UOMs"),
    }


class product_uom(osv.osv):
    _inherit = "product.uom"
    _columns = {
        "code": fields.char("Code", size=32, select=True),
        "sequence" : fields.integer("Sequence")
    }
    _order = "sequence"
    _defaults = {
        "sequence" : 10
    }


class product_category(osv.osv):
    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, list) == False:
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id'] and (not context or context.get("show_parent",True)):
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _complete_name(self, cr, uid, ids, field_name, args, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return dict(res)

    def _relids_product_category(self, cr, uid, ids, context=None):
        res = list(ids)
        res.extend(self.search(cr, uid, [("parent_id", "child_of", ids)]))
        return res


    _inherit = "product.category"
    _columns = {
        "code": fields.char("Code", size=32, select=True),
        "complete_name" : fields.function(_complete_name, type="char", string="Name",store={
                                                 "product.category" : (_relids_product_category,["parent_id", "name"],10),
                                        })
    }
    _order = "complete_name"


class product_template(osv.osv):
    _inherit = "product.template"
    _columns = {
        "name": fields.char("Name", required=True, translate=True, select=True)
    }


class product_product(osv.osv):

    def _get_account_income_standard(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context):
            account = product.product_tmpl_id.property_account_income
            if not account:
                account = product.categ_id.property_account_income_categ

            if account:
                res[product.id]=account.id
            else:
                res[product.id]=None
        return res

    def _get_account_expense_standard(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for product in self.browse(cr, uid, ids, context):
            account = product.product_tmpl_id.property_account_expense
            if not account:
                account = product.categ_id.property_account_expense_categ
            if account:
                res[product.id]=account.id
        return res

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if name:
            ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
            if not ids:
                ptrn=re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

    _inherit = "product.product"
    _columns = {
        "account_income_standard_id" : fields.function(_get_account_income_standard,
                                                    string="Standard income account",type="many2one",relation="account.account"),
        "account_expense_standard_id" : fields.function(_get_account_expense_standard,
                                                    string="Standard expense account",type="many2one",relation="account.account"),
        "name_template": fields.related('product_tmpl_id', 'name', string="Template Name", type='char', store=True, select=True),
    }


class product_pricelist(osv.osv):

    def _active_version(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        date = context and context.get("date",util.currentDate()) or util.currentDate()
        cr.execute(
                "SELECT v.pricelist_id, v.id "
                " FROM product_pricelist_version AS v "
                " WHERE v.pricelist_id IN %s AND active=True "
                "   AND (date_start is NULL OR date_start <= %s) "
                "   AND (date_end is NULL OR date_end >= %s ) "
                " GROUP BY 1,2 ", (tuple(ids),date,date))

        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res


    _inherit = "product.pricelist"
    _columns = {
        "active_version_id" : fields.function(_active_version,string="Active Pricelist",type="many2one"
                                              ,relation="product.pricelist.version"),

    }


class product_supplierinfo(osv.osv):

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if len(ids):
            for obj in self.browse(cr, uid, ids, context):
                res.append((obj.id,obj.name.name))
        return res

    _inherit = "product.supplierinfo"
