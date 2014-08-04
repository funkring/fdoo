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

class product_product(osv.osv):
            
    def auto_ref(self,cr,uid,rec,context):
        return None

    def auto_variant(self,cr,uid,rec,context):
        return None
    
    def support_auto_variant(self,cr,uid,rec,context):
        return False

    def _def_autoref_get(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        calc_ref = []
        cr.execute("SELECT p.id,p.auto_ref,p.default_code FROM product_product AS p WHERE p.id IN %s ",(tuple(ids),))
                                   
        for row in cr.fetchall():
            if row[1]:
                calc_ref.append(row[0])
                res[row[0]]=None
            else:
                res[row[0]]=row[2] or None
        
        if calc_ref:
            for rec in self.browse(cr, uid, calc_ref, context):
                res[rec.id] = self.auto_ref(cr,uid,rec,context)                
        return res
    
    def _def_autoref_set(self,cr,uid,sid,name,value,arg,context=None):
        return cr.execute("UPDATE product_product SET default_code = %s WHERE product_product.id = %s ", (value,sid))
    
    def _def_variants_get(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        calc_ref = []
        cr.execute("SELECT p.id,p.auto_ref,p.variants FROM product_product AS p WHERE p.id IN %s ",(tuple(ids),))
                                   
        for row in cr.fetchall():
            if row[1]:
                calc_ref.append(row[0])
                res[row[0]]=None
            else:
                res[row[0]]=row[2] or None
        
        if calc_ref:
            for rec in self.browse(cr, uid, calc_ref, context):         
                if self.support_auto_variant(cr, uid, rec, context):       
                    res[rec.id] = self.auto_variant(cr,uid,rec,context)                
        return res
    
    def _def_variants_set(self,cr,uid,sid,name,value,arg,context=None):
        return cr.execute("UPDATE product_product SET variants = %s WHERE product_product.id = %s ", (value or None,sid))

      
    _inherit = "product.product"    
    _columns = {       
        "default_code" : fields.function(_def_autoref_get,fnct_inv=_def_autoref_set,store=True,type="char",size=64,string="Reference"),
        "variants" : fields.function(_def_variants_get,fnct_inv=_def_variants_set,store=True,type="char",size=256,string="Variants"), 
        "auto_ref":  fields.boolean("Automatic Reference")
    }
product_product()