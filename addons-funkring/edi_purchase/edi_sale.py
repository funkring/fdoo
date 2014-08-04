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
    
    def _edi_tc_purchase_line_ids(self, cr, uid, order_id, profile):
        edi_link = self.pool.get("edi.link")
        order = self.browse(cr, uid, order_id)
        system = profile.system_id
        remote_purchase_line_ids = []
        for line in order.order_line:
            remote_purchase_line_id = edi_link._remote_id(cr,uid,system.id,"sale.order.line",line.id,remote_model="purchase.order.line")
            if remote_purchase_line_id:
                remote_purchase_line_ids.append(remote_purchase_line_id)
        return remote_purchase_line_ids
    
    def _edi_tc_recheck_order(self, cr, uid, order_id, profile, proxy, context=None):
        link_obj = self.pool.get("edi.link")
        order = self.browse(cr, uid, order_id)
        system = profile.system_id
        remote_order_id = link_obj._remote_id(cr,uid,system.id,self._name,order.id,self._name)
        if remote_order_id:
            remote_server_obj = proxy.get("edi.server_profile")
            remote_server_obj.edi_fv_recheck_order(cr, uid, remote_order_id)
    
    def _edi_tc_purchase_ship_created(self, cr, uid, order_id, profile, proxy, context=None):        
        remote_purchase_line_ids = self._edi_tc_purchase_line_ids(cr,uid,order_id,profile)
        if remote_purchase_line_ids:
            remote_server_obj = proxy.get("edi.server_profile")
            remote_server_obj.edi_fv_purchase_line_confirm(cr,uid,remote_purchase_line_ids)
        return True
                
    def _edi_tc_purchase_shipped(self, cr, uid, order_id, profile, proxy, context=None):        
        remote_purchase_line_ids = self._edi_tc_purchase_line_ids(cr,uid,order_id,profile)
        if remote_purchase_line_ids:
            remote_server_obj = proxy.get("edi.server_profile")
            remote_server_obj.edi_fv_purchase_line_shipped(cr,uid,remote_purchase_line_ids)
        return True
            
    def _edi_tv_order(self, cr, uid, order_id, profile, proxy, context=None):
        supplier = profile.system_id.partner_id
        purchase_line_obj = self.pool.get("purchase.order.line")
        purchase_line_ids = purchase_line_obj.search(cr, uid, [("sale_order_id","=",order_id),("partner_id","=",supplier.id)],context)
        order = []
        for line_id in purchase_line_ids:
            purchase_line = purchase_line_obj._edi_pack_purchase_order_line(cr, uid, line_id, profile, context)
            if purchase_line:
                order.append(purchase_line)
        if order:
            proxy.get("edi.server_profile").edi_fc_order(cr,uid,order) 
        return True      
          
    def _edi_tv_recheck_order(self, cr, uid, order_id, profile, proxy, context=None):
        supplier = profile.system_id.partner_id
        purchase_line_obj = self.pool.get("purchase.order.line")
        purchase_line_ids = purchase_line_obj.search(cr, uid, [("sale_order_id","=",order_id),("partner_id","=",supplier.id)],context)
        order = []
        for line_id in purchase_line_ids:
            purchase_line = purchase_line_obj._edi_pack_purchase_order_line(cr, uid, line_id, profile, context)
            if purchase_line:
                order.append(purchase_line)
        if order:
            proxy.get("edi.server_profile").edi_fc_recheck_order(cr,uid,order_id,order) 
        return True      
                   
    def action_ship_create(self, cr, uid, ids, *args):
        super(sale_order,self).action_ship_create(cr,uid,ids,*args)
        transfer_obj = self.pool.get("edi.transfer")
        purchase_line_obj = self.pool.get("purchase.order.line")        
        for order in self.browse(cr, uid, ids):            
            # execute order recheck
            transfer_obj._call(cr,1,order.partner_id.id,self._name,order.id,self._edi_tc_recheck_order)            
            # execute purchase for suppliers 
            purchase_line_ids = purchase_line_obj.search(cr, uid, [("sale_order_id","=",order.id)])
            suppliers = set()
            for purchase in purchase_line_obj.browse(cr,uid,purchase_line_ids):
                supplier_id = purchase.partner_id.id
                if supplier_id not in suppliers:
                    suppliers.add(supplier_id)
                    transfer_obj._call(cr,uid,supplier_id,self._name,order.id,self._edi_tv_order)
            #execute as admin for notify customer ship created
            transfer_obj._call(cr,1,order.partner_id.id,self._name,order.id,self._edi_tc_purchase_ship_created)           
        return True
   
    def action_ship_end(self, cr, uid, ids, context=None):
        super(sale_order,self).action_ship_end(cr,uid,ids,context)
        transfer_obj = self.pool.get("edi.transfer")
        for order in self.browse(cr, uid, ids):
            #execute as admin for notify customer shipped
            transfer_obj._call(cr,1,order.partner_id.id,self._name,order.id,self._edi_tc_purchase_shipped)            
        return True
            
    _inherit = "sale.order"
sale_order()