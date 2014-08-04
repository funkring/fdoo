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

from openerp.osv import osv,fields


class account_analytic_account(osv.osv):    
    
    def name_get(self, cr, uid, ids, context=None):
        res = super(account_analytic_account,self).name_get(cr,uid,ids,context=context)        
        if ids:
            cr.execute("SELECT a.id, p.name FROM account_analytic_account AS a "
                       " INNER JOIN res_partner AS p ON p.id = a.partner_id "
                       " WHERE a.id IN %s",
                       (tuple(ids),))
            
            partner_names = {}            
            for row in cr.fetchall():
                partner_names[row[0]] = row[1]            
                
            new_res = []
            for value in res:
                cur_id = value[0]
                cur_name = value[1]                
                name = partner_names.get(cur_id)                
                if name:
                    new_res.append((cur_id,cur_name + " [" + name + "]"))                    
                else:
                    new_res.append(value)
                       
            return new_res                 
        return res
      
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):        
        res = super(account_analytic_account,self).name_search(cr,uid,name,args=args,operator=operator,context=context,limit=limit)   
        if not res:
            order_res = self.pool.get("sale.order").name_search(cr,uid,name,args=None,operator=operator,context=context,limit=limit)
            res = []
            if order_res:
                ids = [x[0] for x in order_res]
                analytic_id_for_order = {}
                cr.execute("SELECT id,project_id FROM sale_order WHERE id IN %s AND project_id IS NOT NULL",(tuple(ids),))                
                for row in cr.fetchall():
                    analytic_id_for_order[row[0]]=row[1]                    
                for tup in order_res:
                    analytic_id = analytic_id_for_order.get(tup[0])
                    if analytic_id:
                        res.append((analytic_id,tup[1]))
        return res
    
    _inherit = "account.analytic.account"    
    _columns = {
        "order_id" : fields.many2one("sale.order","Order",ondelete="cascade"),        
    }
