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

import time
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.addons.at_base import util

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)         
        self.pickings = None
        self.move_ids = None
        self.purchase = False
        
        self.localcontext.update({
            "time": time,
            "get_move" : self._get_move,
            "get_address_name" : self._get_address_name,
            "get_address_name2" : self._get_address_name2,
            "get_address" : self._get_address,
            "get_address2" : self._get_address2,
            "get_type" : self._get_type,
            "pickings" : self._get_pickings,
            "purchase_line_images" : self._get_purchase_line_images
        })
        
        
        user = self.localcontext.get("user")
        if user:
            company_rec = user.company_id
            self.localcontext["company"]=company_rec
            if company_rec:
                self.localcontext["company_name"]=company_rec.name
                
        self.picking_in_states = {
            "draft" : _("Draft"),
            "waiting" : _("Waiting"),
            "confirmed" : _("Not Available"),
            "assigned" : _("Assigned"),
            "done" : _("Binned"),
            "cancel" : _("Cancelled")
        }
        
        self.picking_out_states = {
            "draft" : _("Draft"),
            "waiting" : _("Waiting"),
            "confirmed" : _("Not Available"),
            "assigned" : _("Assigned"),
            "done" : _("Dispached"),
            "cancel" : _("Cancelled")
        }
        
    def _get_pickings(self):
        if self.pickings == None:            
            model = util.model_get(self.localcontext)          
            if "purchase.order.line" == model:
                stock_move_obj = self.pool.get("stock.move")                
                picking_obj = self.pool.get("stock.picking")
                purchase_order_line_obj = self.pool.get("purchase.order.line")
                line_ids = [o.id for o in self.objects]                
                move_ids = []
                picking_ids = []
                for line in purchase_order_line_obj.browse(self.cr,self.uid,line_ids,context=self.localcontext):                    
                    move_rec = line.move_dest_id
                    if move_rec:                
                        picking = move_rec.picking_id
                        move_ids.append(move_rec.id)   
                        if picking and picking.id not in picking_ids:
                            picking_ids.append(picking.id)
                    else:
                        for move_rec in stock_move_obj.browse(self.cr,self.uid,stock_move_obj.search(self.cr,self.uid,[("purchase_line_id","=",line.id)]),self.localcontext):
                            picking = move_rec.picking_id
                            move_ids.append(move_rec.id)                   
                            if picking and picking.id not in picking_ids:
                                picking_ids.append(picking.id)
                            
                self.pickings = picking_obj.browse(self.cr,self.uid,picking_ids,self.localcontext)
                self.move_ids = move_ids
                self.purchase = True
            elif model and model.startswith("stock.picking"):
                self.pickings = self.objects
            else:
                self.pickings = []                
        return self.pickings
    
    def _get_address(self,picking):
        return picking.address_id
      
    def _get_address_name(self,picking):
        if picking.type == "out":
            return _("Delivery Address")
        elif picking.type == "in":
            return _("Sender Address")
        else:
            return _("Address")
        
    def _get_address2(self,picking):
        if picking.type == "out":
            return picking.sender_address_id
        else:
            return picking.location_address_id
                
    def _get_address_name2(self,picking):
        if picking.type == "out":
            return _("Sender Address")
        elif picking.type == "in":
            return _("Delivery Address")
        else:
            return _("Address")
    
    def _get_type(self,picking):
        if picking.type == "out":
            return _("Delivery Note")
        elif picking.type == "in":
            return _("Running Note")
        elif picking.type == "intern":
            return _("Internal Note")
        else:
            return picking.type
    
    def _get_location(self,picking,picking_line):
        location = ""
        if picking.type == "out":
            if picking_line.location_id:
                location = picking_line.location_id.name
        else:
            if picking_line.location_dest_id:
                location = picking_line.location_dest_id.name                        
        return location
    
    def _get_state(self,picking,picking_line):
        if picking.type == "out":
            return self.picking_out_states.get(picking_line.state,picking_line.state)
        else:
            return self.picking_in_states.get(picking_line.state,picking_line.state)
    
       
    def _get_purchase_line_images(self,prep_line):
        res = prep_line.get("purchase_line_images")
        if res == None:
            line = prep_line.get("line")
            purchase_line = prep_line.get("purchase_line")
            res = []
            if line and purchase_line:               
                attachment_obj = self.pool.get("ir.attachment")
                ids = attachment_obj.search(self.cr,self.uid,[("res_model","=","purchase.order.line"),("res_id","=",purchase_line.id),("name","=","referenz.jpg")],limit=1)                     
                for attachment in attachment_obj.browse(self.cr,self.uid,ids,self.localcontext):
                    try:
                        res.append(attachment.datas)
                    except IOError:
                        pass    
            prep_line["purchase_line_images"]=res                        
        return res
        
        
   
    def _get_move(self,picking):       
        move_lines = []
        move_lines_other = []
        origin = []
        
        def addOrigin(inOrigin):
            if inOrigin:
                for originToken in inOrigin.split(":"):
                    if not originToken in origin:
                        origin.append(originToken)
                    
        total = 0.0
        uom = None
        purchase_line_obj = self.pool.get("purchase.order.line")
                        
        for line in picking.move_lines:     
            if self.move_ids == None or line.id in self.move_ids:          
                name = line.name or (line.product_id and line.product_id.name) or ""
                variant = (line.product_id and line.product_id.variants) or ""
                note = None
                nameToken = name.split(" - ")
                if len(nameToken) >= 2:
                    name = nameToken[0]
                    variant = " - ".join(nameToken[1:])
                    
                sale_line = line.sale_line_id
                purchase_line = line.purchase_line_id       
                if not purchase_line:
                    ids = purchase_line_obj.search(self.cr,self.uid,[("move_dest_id","=",line.id)],limit=1)
                    purchase_line = ids and purchase_line_obj.browse(self.cr,self.uid,ids[0],self.localcontext) or None
                
                if purchase_line:
                    addOrigin(purchase_line.origin)
                    if self.purchase:                    
                        note = purchase_line.notes
                    
                #if sale_line and not self.purchase:
                #    note = sale_line.notes
                                                                    
                prep_line = {                            
                    "line" : line,
                    "purchase_line" : purchase_line,
                    "code" : (line.product_id and line.product_id.default_code) or "",
                    "name" : name,
                    "note" : note,
                    "variants" : variant,
                    "lot" : (line.prodlot_id and line.prodlot_id.name) or "",
                    "state" : self._get_state(picking,line),
                    "location" : self._get_location(picking,line),                    
                    "qty" : line.product_qty or 0.0,
                    "uom" : (line.product_uom and line.product_uom.name) or "" 
                }
                                
                total+=line.product_qty
                if not uom:
                    uom = prep_line.get("uom")
                           
#                if line.state in ("assigned","done"):
#                    if picking.type != "out" or line.state == "done":
#                        move_lines.append(prep_line)                            
#                else:
#                    move_lines_other.append(prep_line)

                if line.state in ("assigned","done","confirmed"):
                    move_lines.append(prep_line)                            
                else:
                    move_lines_other.append(prep_line)                                              
        
        addOrigin(picking.origin)                    
        
        return [{
          "origin" : ":".join(origin),
          "move_lines" : move_lines,
          "move_lines_other" : move_lines_other,          
          "total" : total,
          "uom" : uom or ""
        }]