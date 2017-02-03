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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class bonus(osv.osv):
        
    _columns = {
        "name" : fields.char("Name",size=64,required=True,translate=True),
        "line_ids" : fields.one2many("commission_sale.bonus_line","bonus_id","Bonus Lines")
    }    
    _name="commission_sale.bonus"
    _description="Sales Bonus"


class bonus_line(osv.osv):
    
    _columns = {   
        "name" : fields.char("Name",size=64,required=True,translate=True),        
        "bonus_id" : fields.many2one("commission_sale.bonus","Sales Bonus",required=True,select=True,ondelete="cascade"),
        "volume_of_sales" : fields.float("Volume of Sales",digits_compute=dp.get_precision("Sale Price"),required=True),
        "bonus" : fields.float("Bonus %",help="Bonus = Volume of Sales * Bonus %",required=True)
    }
    _name = "commission_sale.bonus_line"
    _description="Sales Bonus Line"
    _order = "volume_of_sales"


class crm_case_section(osv.osv):
        
    _columns = {
        "sales_commission" : fields.float("Commission %"),
        "commission_rule_ids" : fields.one2many("commission_sale.rule","section_id","Commission Rules"),
        "sales_bonus_id" : fields.many2one("commission_sale.bonus","Sales Bonus"),
        "property_commission_product" : fields.property(type="many2one",
                                                        relation="product.product",
                                                        string="Invoice Product"),
        "property_analytic_journal" : fields.property(type="many2one",
                                                      relation="account.analytic.journal",
                                                      string="Commission Journal")
                
    }    
    _inherit = "crm.case.section"
    

class commission_rule(osv.osv):
    
    def _get_rule(self, cr, uid, section, product, context=None):
        res = None
        if section and product:
            res = self.search_read(cr, uid, [("section_id","=",section.id),("product_id","=",product.id)], ["commission"], context=context)
            if not res:
                res = self.search_read(cr, uid, [("section_id","=",section.id),("categ_id","=",product.categ_id.id)], ["commission"], context=context)
        return res and res[0] or None
    
    _name = "commission_sale.rule"
    _description = "Sale Commission Rules"
    _rec_name = "sequence"
    _columns = {
        "section_id" : fields.many2one("crm.case.section", "Section", required=True),
        "sequence" : fields.integer("Sequence"),
        "categ_id" : fields.many2one("product.category","Category"),
        "product_id" : fields.many2one("product.product","Product"),
        "commission" : fields.float("Commission %")
    }
    _order = "section_id, sequence"
    
