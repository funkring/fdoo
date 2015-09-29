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
        
        self.localcontext.update({
            "time": time,
            "get_move" : self._get_move,
            "get_address_name" : self._get_address_name,
            "get_address_name2" : self._get_address_name2,
            "get_address" : self._get_address,
            "get_address2" : self._get_address2,
            "get_type" : self._get_type,
            "get_doc" : self._get_doc,
            "get_images" : self._get_images
        })


        user = self.localcontext.get("user")
        if user:
            company_rec = user.company_id
            self.localcontext["company"]=company_rec
            if company_rec:
                self.localcontext["company_name"]=company_rec.name

        self.picking_in_states = {
            "draft" : _("New"),
            "waiting" : _("Waiting Another Move"),
            "confirmed" : _("Waiting Availability"),
            "assigned" : _("Available"),
            "done" : _("Done"),
            "cancel" : _("Cancelled")
        }

        self.picking_out_states = {
            "draft" : _("New"),
            "waiting" : _("Waiting Another Move"),
            "confirmed" : _("Waiting Availability"),
            "assigned" : _("Available"),
            "done" : _("Done"),
            "cancel" : _("Cancelled")
        }
    
    def _all_pickings(self):
        return False
    
    def _get_doc(self):        
        pickings = None
        move_ids = None
        
        model = util.model_get(self.localcontext)
        if "purchase.order.line" == model or "purchase.order" == model:
            
            stock_move_obj = self.pool.get("stock.move")
            picking_obj = self.pool.get("stock.picking")
            purchase_order_line_obj = self.pool.get("purchase.order.line")
            
            # get line ids
            line_ids = None
            if "purchase.order" == model:
                line_ids = []
                for order in self.objects:
                    for line in order.order_line:
                        line_ids.append(line.id)
            else:
                line_ids = [o.id for o in self.objects]
            
            move_ids = set()
            picking_ids = []
            
             
            # reload lines
            for line in purchase_order_line_obj.browse(self.cr, self.uid, line_ids, context=self.localcontext):
                
                for move in line.move_ids:
                
                    cur_move = move
                    next_picking = True

                    # get pickings to move                    
                    picking = move.picking_id
                    if picking:
                        next_picking = self._all_pickings()
                        picking = cur_move.picking_id
                        move_ids.add(cur_move.id)
                        if picking and picking.id not in picking_ids:
                            picking_ids.append(picking.id)
                    
                    # get pickings to destination move
                    cur_move = cur_move.move_dest_id
                    if next_picking:
                        next_picking = self._all_pickings()
                        picking = cur_move.picking_id
                        move_ids.add(cur_move.id)
                        if picking and picking.id not in picking_ids:
                            picking_ids.append(picking.id)
                            
                    # search other
                    if next_picking:
                        for cur_move in stock_move_obj.browse(self.cr,self.uid,stock_move_obj.search(self.cr,self.uid,[("purchase_line_id","=",line.id)]),self.localcontext):
                            picking = cur_move.picking_id
                            move_ids.add(cur_move.id)
                            if picking and picking.id not in picking_ids:
                                picking_ids.append(picking.id)

            # results
            pickings = picking_obj.browse(self.cr, self.uid,picking_ids, self.localcontext)
            move_ids = move_ids
            
        elif model and model.startswith("stock.picking"):
            pickings = self.objects
        else:
            pickings = []
                
        return [{
            "pickings" : pickings,
            "move_ids" : move_ids
        }]
   
    def _get_address(self,picking):
        if picking.simple_type == "dropshipment":
            sale_order = picking.sale_id
            if sale_order:
                return sale_order.partner_shipping_id        
        return picking.partner_id
    
    def _get_address_name(self,picking):
        if picking.simple_type in ("outgoing","dropshipment"):
            return _("Delivery Address")
        elif picking.simple_type == "incoming":
            return _("Sender Address")
        else:
            return _("Address")

    def _get_address2(self, picking):
        if picking.simple_type in ("outgoing","dropshipment"):
            return picking.sender_address_id
        else:
            partner = None
            if picking.location_id:
                partner = picking.location_id.partner_id
            if not partner:
                partner = picking.company_id.partner_id
            return partner

    def _get_address_name2(self,picking):
        if picking.simple_type in ("outgoing","dropshipment"):
            return _("Sender Address")
        elif picking.simple_type == "incoming":
            return _("Delivery Address")
        else:
            return _("Address")

    def _get_type(self,picking):
        if picking.simple_type in ("outgoing","dropshipment","incoming"):
            return _("Delivery Note")
        else:
            return picking.picking_type_id.name

    def _get_location(self,picking,picking_line):
        location = ""
        if picking.simple_type == "outgoing":
            if picking_line.location_id:
                location = picking_line.location_id.name
        else:
            if picking_line.location_dest_id:
                location = picking_line.location_dest_id.name
        return location

    def _get_state(self,picking,picking_line):
        if picking.simple_type in ("outgoing","dropshipment"):
            return self.picking_out_states.get(picking_line.state,picking_line.state)
        else:
            return self.picking_in_states.get(picking_line.state,picking_line.state)

    
    def _get_images(self,prep_line):
        res = prep_line.get("images")
        if res is None:
            line = prep_line.get("line")
            purchase_line = prep_line.get("purchase_line")
            res = []
            if line and purchase_line:
                attachment_obj = self.pool.get("ir.attachment")
                ids = attachment_obj.search(self.cr,self.uid,[("res_model","=","purchase.order"),("res_id","=",purchase_line.order_id.id),"|",("name","ilike",".jpg"),("name","ilike",".png")])
                for attachment in attachment_obj.browse(self.cr,self.uid,ids,self.localcontext):
                    datas = attachment.datas
                    if datas:
                        res.append(datas)
            prep_line["images"]=res
        return res
    
    def _get_move(self, doc, picking):
        lines = []
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
        move_ids = doc.get("move_ids", None)

        for line in picking.move_lines:
            # check if move is valid
            if move_ids is None or line.id in move_ids:
                name = line.name or (line.product_id and line.product_id.name) or ""
                note = line.note
                prep_line = {
                    "line" : line,
                    "line_code" : "SM%s" % str(line.id),
                    "code" : (line.product_id and line.product_id.default_code) or "",
                    "name" : name,
                    "note" : note,
                    "state" : self._get_state(picking,line),
                    "location" : self._get_location(picking,line),
                    "qty" : line.product_qty or 0.0,
                    "uom" : (line.product_uom and line.product_uom.name) or ""
                }

                total+=line.product_qty
                if not uom:
                    uom = prep_line.get("uom")

                if line.state in ("assigned","done","confirmed"):
                    move_lines.append(prep_line)
                else:
                    move_lines_other.append(prep_line)
                    
                lines.append(prep_line)

        addOrigin(picking.origin)

        packages = []
        package_count = picking.number_of_packages or 1
        for package in range(1,package_count+1):
            packages.append({
                "code" : "SP%sP%sP%s" % (picking.id, package, package_count),
                "package" : package
            })
                 
        weight = None
        if picking.weight:
            weight_uom = picking.weight_uom_id and picking.weight_uom_id.name or _("KG")
            weight = "%s %s" % (self.formatLang(picking.weight,digits=3), weight_uom)
        
        address_id = self._get_address(picking)
        address_name = self._get_address_name(picking)          
        address2_id = self._get_address2(picking)
        address2_name = self._get_address_name2(picking)
                   
        return [{
          "address_id" : address_id,
          "address_name" : address_name,
          "address2_id" : address2_id,
          "address2_name" : address2_name,
          "weight" : weight,
          "origin" : ":".join(origin),
          "packages" : packages,
          "lines" : lines,
          "move_lines" : move_lines,
          "move_lines_other" : move_lines_other,
          "total" : total,
          "uom" : uom or "",
          "newpage" : doc["pickings"][-1].id != picking.id
        }]