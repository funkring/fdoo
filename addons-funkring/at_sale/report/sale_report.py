# -*- coding: utf-8 -*-
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

class sale_report(osv.Model):
    
    def _select(self):
        select_str = super(sale_report, self)._select()
        select_str += """
                ,s.shop_id AS shop_id
                ,ay.root_account_id AS root_analytic_id   
                ,( SELECT SUM(hal.amount) FROM account_analytic_line hal 
                    WHERE hal.account_id = s.project_id ) AS post_calc
        """ 
        return select_str
    
    def _from(self):
        from_str = super(sale_report, self)._from()
        from_str += """
            LEFT JOIN account_analytic_account ay ON ay.id = s.project_id 
            LEFT JOIN account_analytic_line ayl ON ayl.account_id = ay.id  
        """
        return from_str
        
    def _group_by(self):
        group_str = super(sale_report, self)._group_by()
        group_str += """
                ,s.shop_id
                ,ay.root_account_id
        """
        return group_str
    
    _inherit = "sale.report"
    _columns = {
        'root_analytic_id': fields.many2one('account.analytic.account', 'Main Analytic Account', readonly=True),
        "shop_id" : fields.many2one("sale.shop","Shop", readonly=True),
        "post_calc" : fields.float("Post Calculation", readonly=True)
    }