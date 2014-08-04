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
from datetime import date, timedelta

class delivery_today_wizard(osv.osv_memory):
    
    def do_print(self, cr, uid, ids, *args):
        for wizard in self.browse(cr, uid, ids):
            
            params = []
            if wizard.level_id:
                params.append("AND pl.level_id = %s" % (wizard.level_id.id,) )
            if wizard.shop_id:
                params.append("AND pl.shop_id = %s" % (wizard.shop_id.id,) )
            
            query = (" SELECT pl.id FROM purchase_order_line pl " 
                    " LEFT JOIN res_partner_address a ON a.id = pl.dest_address_id "
                    " WHERE pl.state IN ('confirmed','done') "
                    " AND pl.write_date >= '%s' "
                    " AND pl.write_date <  '%s' "
                    " %s "
                    " ORDER BY a.name desc" % (wizard.date_from, wizard.date_to, " ".join(params)))
            cr.execute(query)
            
            ids = self.pool.get("purchase.order.line").search(cr,uid,[("id","in",[r[0] for r in cr.fetchall()])])
            if ids:
                datas = {
                     "ids" : ids,
                     "model": "purchase.order.line"    
                }
                return {
                    "type": "ir.actions.report.xml",
                    "report_name": "purchase.order.line",
                    "datas": datas
                }   
            return { "type" : "ir.actions.act_window_close" }
    
    _name = "supplier_area.delivery_today_wizard"
    _description = "Deliveries Today"
    
    _columns = {
        "shop_id" :fields.many2one("sale.shop","Shop"),
        "level_id" : fields.many2one("purchase.order_level","Level"),
        "date_from" : fields.date("From", required=True),
        "date_to" : fields.date("To", required=True)
    }
    
    _defaults = {
        "date_from" : str(date.today()),
        "date_to" : str(date.today()+timedelta(days=1))
    }
delivery_today_wizard()