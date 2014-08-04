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
import decimal_precision as dp

class bonus(osv.osv):
        
    _columns = {
        "name" : fields.char("Name",size=64,required=True,translate=True),
        "line_ids" : fields.one2many("at_commission_sale.bonus_line","bonus_id","Bonus Lines")
    }    
    _name="at_commission_sale.bonus"
    _description="Sales Bonus"
bonus()


class bonus_line(osv.osv):
    
    _columns = {   
        "name" : fields.char("Name",size=64,required=True,translate=True),        
        "bonus_id" : fields.many2one("at_commission_sale.bonus","Sales Bonus",required=True,select=True,ondelete="cascade"),
        "sequence" : fields.integer("Sequence"),
        "volume_of_sales" : fields.float("Volume of Sales",digits_compute=dp.get_precision("Sale Price"),required=True),
        "bonus" : fields.float("Bonus %",help="Bonus = Volume of Sales * Bonus %",required=True)
    }
    _name = "at_commission_sale.bonus_line"
    _description="Sales Bonus Line"
    _order = "bonus_id, sequence"
bonus_line()


class crm_case_section(osv.osv):
        
    _columns = {
        "sales_commission" : fields.float("Commission %"),
        "sales_bonus_id" : fields.many2one("at_commission_sale.bonus","Sales Bonus"),
        "property_commission_product" : fields.property("product.product",type="many2one",
                                                            relation="product.product",
                                                            string="Invoice Product",

                                                            view_load=True,
                                                            group_name="Commission Properties"
                                                            ),
        "property_analytic_journal" : fields.property("account.analytic.journal",type="many2one",
                                                      relation="account.analytic.journal",
                                                      string="Commission Journal",

                                                      view_load=True,
                                                      group_name="Commission Properties")
                
    }    
    _inherit = "crm.case.section"
crm_case_section()