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

class product_attribute_template(osv.osv):    
    _name = "product.pr_attribute_template"
    _description = "Product Attribute Template"
    _columns = {
        "name" : fields.char("Name",size=64,required=True),
        "code" :fields.char("Code",size=16,required=True)
    }    
product_attribute_template()


class product_format(osv.osv):        
    _inherit = "product.pr_attribute_template"
    _name = "product.pr_format"
    _description = "Format"            
product_format()


class product_leteral_pressure(osv.osv):        
    _inherit = "product.pr_attribute_template"
    _name = "product.pr_leteral_pressure"
    _description = "Leteral Pressure"            
product_leteral_pressure()


class product_gram(osv.osv):        
    _inherit = "product.pr_attribute_template"
    _name = "product.pr_gram"
    _description = "Gram"            
product_gram()


class product_material(osv.osv):        
    _inherit = "product.pr_attribute_template"
    _name = "product.pr_material"
    _description = "Material"            
product_material()


class product_material_surface(osv.osv):        
    _inherit = "product.pr_attribute_template"
    _name = "product.pr_material_surface"
    _description = "Material Surface"            
product_material_surface()


class product_orientation(osv.osv):        
    _inherit = "product.pr_attribute_template"
    _name = "product.pr_orientation"
    _description = "Orientation"            
product_orientation()


class product_color(osv.osv):        
    _inherit = "product.pr_attribute_template"
    _name = "product.pr_color"
    _description = "Color"            
product_color()


class product_attribute(osv.osv):        
    _inherit = "product.pr_attribute_template"
    _name = "product.pr_attribute"
    _description = "Attribute"            
product_attribute()


class product(osv.osv):

    def support_auto_variant(self,cr,uid,rec,context):
        return True
    
    def auto_variant(self,cr,uid,rec,context):
        tokens  = []
                
        def add(code):
            if code:
                tokens.append(code)
        
        def addnum(num):
            if num:
                value = int(num)
                add("%05.0f" % value)
        
        def addattr(code_rec):
            if code_rec:
                add(code_rec.name)
        
        addnum(rec.pr_unit)
        addattr(rec.pr_format_id)
        addattr(rec.pr_leteral_pressure_id)
        addattr(rec.pr_material_id)
        addattr(rec.pr_material_surface_id)
        addattr(rec.pr_gram_id)
        addattr(rec.pr_orientation_id)
        addattr(rec.pr_color_id)        

        for attrib in rec.pr_attribute_ids:
            addattr(attrib)
                    
        return " ".join(tokens) or None
    

    def auto_ref(self,cr,uid,rec,context):
        tokens  = []
                
        def add(code):
            if code:
                tokens.append(code)
        
        def addnum(num):
            if num:
                value = int(num)
                add("%05.0f" % value)
        
        def addattr(code_rec):
            if code_rec:
                add(code_rec.code)
            
        addattr(rec.categ_id)
        addnum(rec.pr_unit)
        add(rec.shortcut)
        addattr(rec.pr_format_id)
        addattr(rec.pr_leteral_pressure_id)
        addattr(rec.pr_material_id)
        addattr(rec.pr_material_surface_id)
        addattr(rec.pr_gram_id)
        addattr(rec.pr_orientation_id)
        addattr(rec.pr_color_id)        

        for attrib in rec.pr_attribute_ids:
            addattr(attrib)
                    
        return "".join(tokens) or None


    _inherit = "product.product" 
    _columns = {      
        "pr_unit" : fields.float("Print Unit"),
        "pr_format_id" : fields.many2one("product.pr_format","Format"),
        "pr_leteral_pressure_id" : fields.many2one("product.pr_leteral_pressure","Leteral Pressure"),
        "pr_gram_id" : fields.many2one("product.pr_gram","Gram"),
        "pr_material_id" : fields.many2one("product.pr_material","Material"),
        "pr_material_surface_id" : fields.many2one("product.pr_material_surface","Material Surface"),
        "pr_orientation_id" : fields.many2one("product.pr_orientation","Orientation"),
        "pr_color_id" : fields.many2one("product.pr_color","Color"),
        "pr_attribute_ids" : fields.many2many("product.pr_attribute","product_pr_attribute_rel","product_id","pr_attribute_id","Attributes")
    }   
product()