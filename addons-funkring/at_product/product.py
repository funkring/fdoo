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
        "sequence" : fields.integer("Sequence"),
        "nounit" : fields.boolean("No Unit")
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


class product_product(osv.osv):

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if name:
            ids = self.search(cr, user, [('default_code','ilike',name)]+ args, limit=limit, context=context)
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
    
class product_pricelist_version(osv.osv):
    
    def _pricelist_view(self, cr, uid, version, context=None):
        product_map = {}
        category_list = []
        products_by_qty_by_partner = []
        category_map = {}
        
        def add_product(product):
            if not product.id in product_map:
                product_vals = {
                    "product" : product,
                    "price" :  product.list_price
                }
                # set to product map
                product_map[product.id] = product_vals         
                products_by_qty_by_partner.append((product, 1, None))       
                # check if category exist
                category_vals = category_map.get(product.categ_id.id)
                if not category_vals:
                    category_vals = {
                        "name" : product.categ_id.name,
                        "products" : []
                    }
                    category_list.append(category_vals)
                    category_map[product.categ_id.id]=category_vals
                    
                category_vals["products"].append(product_vals)
            
        
        for item in version.items_id:
            product = item.product_id                   
            if product:
                add_product(product)      
                
        # determine price
        pricelist_obj = self.pool.get("product.pricelist")
        price_dict = pricelist_obj._price_get_multi(cr, uid, version, products_by_qty_by_partner, context)
        for product_id, price in price_dict.items():
            product_vals = product_map.get(product_id)
            if product_vals and price:
                product_vals["price"]=price
                
        return {
            "name" : version.name,
            "categories" : category_list,
            "currency" : version.pricelist_id.currency_id
        }
    
    _inherit = "product.pricelist.version"


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
    _columns = {
        "cost_price" : fields.float("Cost price")
    }









