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

class commission_line(osv.osv):
    
    def _get_sale_commission(self, cr, uid, price_subtotal, percent, context=None):
        if percent: 
            factor = percent / 100.0
            return factor*price_subtotal               
        return 0
    
    def _update_bonus(self, cr, uid, salesman_ids, period_ids, context=None):
        #
        if not salesman_ids or not period_ids:
            return 
        #
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
                if bonus_line.volume_of_sales <= total:
                    bonus = bonus_line
                    continue
                break
                        
            if not bonus:
                line_ids = commission_line_obj.search(cr,uid,[("period_id","=",period_id),
                                                              ("partner_id","=",partner_id),
                                                              ("invoiced_id","=",False),
                                                              ("sales_bonus_line_id","!=",False)])
                
                for cl in commission_line_obj.browse(cr,uid,line_ids,context):
                    amount = self._get_sale_commission(cr, uid, cl.price_sub, cl.base_commission, context=context)
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
                    amount = self._get_sale_commission(cr, uid, cl.price_sub, total_commission, context=context)
                    commission_line_obj.write(cr,uid,[cl.id], {
                        "total_commission" : total_commission,
                        "amount" : amount,
                        "sales_bonus_line_id" : bonus.id                             
                    },context)
    
    _columns = {
        "salesman_id" : fields.many2one("res.users","Salesman",ondelete="restrict"),
        "sales_bonus_line_id" : fields.many2one("commission_sale.bonus_line","Sales Bonus",ondelete="restrict")
    }    
    _inherit = "commission.line"
    
    