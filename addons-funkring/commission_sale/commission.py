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
from openerp.tools.translate import _

class commission_line(osv.osv):
    
    def _update_bonus(self, cr, uid, salesman_ids, period_ids, context=None):
        if not salesman_ids or not period_ids:
            return 

        period_id = None
        partner_id = None
        team_id = None
        team = None
         
        team_obj = self.pool.get("crm.case.section")
        commission_line_obj = self.pool.get("commission.line")
         
        cr.execute("SELECT s.id team_id, cl.period_id, cl.partner_id, SUM(cl.price_sub) "
                   " FROM commission_line cl "
                   " INNER JOIN res_users u ON u.id = cl.salesman_id "
                   " INNER JOIN crm_case_section s ON s.id = u.default_section_id "
                   " WHERE cl.salesman_id IN %s "
                   "   AND cl.period_id IN %s "
                   " GROUP BY 1,2,3 "
                   " ORDER BY 1,2,3 "
                   ,(tuple(salesman_ids),tuple(period_ids)))
                                  
        for row in cr.fetchall():            
            # grouped by section
            if team_id != row[0]:                
                team_id = row[0]
                team = team_obj.browse(cr,uid,team_id,context)                
            period_id = row[1]
            partner_id = row[2]
            total = row[3]
            #
            sale_bonus = team.sales_bonus_id
            if not sale_bonus:
                continue
            #            
            bonus = None
            for bonus_line in sale_bonus.line_ids:
                if total >= bonus_line.volume_of_sales:
                    bonus = bonus_line
                else:                    
                    break
                         
            if not bonus:
                line_ids = commission_line_obj.search(cr,uid,[("period_id","=",period_id),
                                                              ("partner_id","=",partner_id),
                                                              ("invoiced_id","=",False),
                                                              ("sales_bonus_line_id","!=",False)])
                 
                for cl in commission_line_obj.browse(cr,uid,line_ids,context):
                    amount = cl.price_sub * (cl.base_commission / 100.0)*-1.0
                    commission_line_obj.write(cr,uid,[cl.id], {  
                        "total_commission" : cl.base_commission,                                                            
                        "amount" : amount,
                        "sales_bonus_line_id" : None                             
                    },context)
            elif bonus:
                line_ids = commission_line_obj.search(cr,uid,[("period_id","=",period_id),
                                                              ("partner_id","=",partner_id),
                                                              ("invoiced_id","=",False),
                                                              '|',
                                                              ("sales_bonus_line_id","!=",bonus.id),
                                                              ("sales_bonus_line_id","=",False)])
                 
                for cl in commission_line_obj.browse(cr,uid,line_ids,context):
                    total_commission=cl.base_commission+bonus.bonus
                    amount = cl.price_sub * (total_commission / 100.0)*-1.0
                    commission_line_obj.write(cr,uid,[cl.id], {
                        "total_commission" : total_commission,
                        "amount" : amount,
                        "sales_bonus_line_id" : bonus.id                             
                    },context)
                    
        return True
    
    def _get_sale_commission(self, cr, uid, name, user, customer, product, qty, netto, date, pricelist=None, defaults=None, period=None, context=None):
        res = []
        
        period_obj = self.pool["account.period"]        
        pricelist_obj = self.pool.get("product.pricelist")
        pricelist_item_obj = self.pool.get("product.pricelist.item")
        rule_obj = self.pool.get("commission_sale.rule")
        
        team = user.default_section_id
        partner = user.partner_id
        
        #check partner and team
        if not partner or not team:
            return res
        
        # get percent
        percent = product.commission_percent
        if not percent:
            percent = product.categ_id.commission_percent
        if not percent:
            percent = team.sales_commission
            
        # provision product
        prov_prod = product.commission_prod_id
        if not prov_prod:
            prov_prod = product.categ_id.commission_prod_id
                    
        # search for rule                                                               
        rule = rule_obj._get_rule(cr, uid, team, product, context=context)
        if rule:
            percent = rule.get("commission",0.0) or 0.0
        elif pricelist:
            # search for pricelist rule
            item_id = pricelist_obj.price_rule_get(cr, uid, [pricelist.id], product.id, qty,
                                partner=customer.id,context=context)[pricelist.id][1]
            
            if item_id:
                prule = pricelist_item_obj.read(cr, uid, item_id, ["commission_active","commission"], context=context)
                if prule.get("commission_active"):
                    percent = prule.get("commission",0.0) or 0.0
        
        if percent:
            factor = (percent / 100.0)*-1
            
            period_id = period and period.id or None
            if not period_id:
                period_id = period_obj.find(cr, uid, dt=date, context=context)[0]
            
            commission_product = team.property_commission_product
            journal = team.property_analytic_journal
            
            entry = {}
            if defaults:
                entry.update(defaults)
            entry.update({
                "date": date,
                "name": _("Sales Commission: %s") % self._short_name(name),
                "unit_amount": qty,
                "amount": netto*factor,
                "base_commission" : percent,
                "total_commission" : percent,
                "product_id": commission_product.id,
                "product_uom_id": commission_product.uom_id.id,
                "general_account_id": commission_product.account_income_standard_id.id,
                "journal_id": journal.id,
                "partner_id" : partner.id,
                "user_id" : uid,
                "period_id" : period_id,
                "price_sub" : netto,
                "salesman_id" : user.id,
                "sale_partner_id" : customer.id,
                "sale_product_id" : product.id
            })
            res.append(entry)
                
        if prov_prod:
            period_id = period and period.id or None
            if not period_id:
                period_id = period_obj.find(cr, uid, dt=date, context=context)[0]
            
            journal = team.property_analytic_journal
            
            pricelist = partner.property_product_pricelist
            price = prov_prod.lst_price
            
            if pricelist:
                price = pricelist_obj.price_get(cr, uid, [pricelist.id], prov_prod.id, qty, partner=partner, context=context)[pricelist.id]
            
            # amount with correct sign
            amount = price*qty*-1
            percent = 0.0
            if amount:
                percent = abs((100.0/netto)*amount)
                
            # if customer refund than turn sign
            if netto < 0:
                amount *= -1
            
            entry = {}
            if defaults:
                entry.update(defaults)
                
            entry.update({
                "date": date,
                "name": _("Sales Commission: %s") % self._short_name(name),
                "unit_amount": qty,
                "amount": amount,
                "base_commission" : percent,
                "total_commission" : percent,
                "product_id": prov_prod.id,
                "product_uom_id": prov_prod.uom_id.id,
                "general_account_id": prov_prod.account_income_standard_id.id,
                "journal_id": journal.id,
                "partner_id" : partner.id,
                "user_id" : uid,
                "period_id" : period_id,
                "price_sub" : netto,
                "salesman_id" : user.id,
                "sale_partner_id" : customer.id,
                "sale_product_id" : product.id,
                "val_based" : True
            })
            res.append(entry)
            
        return res
    
    _columns = {
        "salesman_id" : fields.many2one("res.users","Salesman",ondelete="restrict"),
        "sales_bonus_line_id" : fields.many2one("commission_sale.bonus_line","Sales Bonus",ondelete="restrict")
    }    
    _inherit = "commission.line"
    
    