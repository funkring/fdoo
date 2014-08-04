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

from openerp.osv import osv

class sale_order(osv.osv):
    
    def onchange_partner_id2(self, cr, uid, ids, part_id, shop_id):
        res = super(sale_order,self).onchange_partner_id2(cr, uid, ids, part_id, shop_id)
        if part_id:
            partner = self.pool.get("res.partner").browse(cr,uid,part_id)
            section = partner.section_id
            if section:
                members = section.member_ids                
                if members:
                    member_ids = [m.id for m in members]
                    if uid in member_ids:
                        res["value"]["user_id"]=uid
                    else:            
                        res["value"]["user_id"]=member_ids[0]
        return res
    
    
    _inherit = "sale.order"
sale_order()