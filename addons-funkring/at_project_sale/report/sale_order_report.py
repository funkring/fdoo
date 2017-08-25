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
from openerp import tools

class sale_order_report(osv.osv):
    _name = "sale.order.report"
    _description = "Sales Order Statistics"
    _auto = False
    _rec_name = "date"

    _columns = {
        "order_id" : fields.many2one("sale.order","Sale Order", readonly=True),
        "date": fields.datetime("Date Order", readonly=True),  
        "date_confirm": fields.date("Date Confirm", readonly=True),
        "partner_id": fields.many2one("res.partner", "Partner", readonly=True),
        "company_id": fields.many2one("res.company", "Company", readonly=True),
        "user_id": fields.many2one("res.users", "Salesperson", readonly=True),
        "amount_untaxed": fields.float("Total", readonly=True),
        "state": fields.selection([
            ("cancel", "Cancelled"),
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("exception", "Exception"),
            ("done", "Done")], "Order Status", readonly=True),
        "pricelist_id": fields.many2one("product.pricelist", "Pricelist", readonly=True),
        "analytic_account_id": fields.many2one("account.analytic.account", "Project", readonly=True),
        "section_id": fields.many2one("crm.case.section", "Sales Team", readonly=True),
        "root_analytic_id": fields.many2one("account.analytic.account", "Main Analytic Account", readonly=True),
        "shop_id" : fields.many2one("sale.shop","Shop", readonly=True)
    }
    _order = "date desc"

    def _select(self):
        select_str = """
             SELECT  o.id as id                    
                    ,o.shop_id as shop_id
                    ,ay.root_account_id as root_analytic_id
                    ,o.id as order_id                 
                    ,o.date_order as date
                    ,o.date_confirm as date_confirm
                    ,o.partner_id as partner_id
                    ,o.user_id as user_id
                    ,o.company_id as company_id
                    ,o.state
                    ,o.pricelist_id as pricelist_id
                    ,o.project_id as analytic_account_id
                    ,o.section_id as section_id
                    ,SUM(o.amount_untaxed) AS amount_untaxed                    
        """
        return select_str

    def _from(self):
        from_str = """
                sale_order o
                LEFT JOIN account_analytic_account ay ON ay.id = o.project_id 
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                    o.shop_id,
                    ay.root_account_id,
                    o.id,
                    o.date_order,
                    o.date_confirm,
                    o.partner_id,
                    o.user_id,
                    o.company_id,
                    o.state,
                    o.pricelist_id,
                    o.project_id,
                    o.section_id
        """
        return group_by_str

    def init(self, cr):
        # self._table = sale_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

