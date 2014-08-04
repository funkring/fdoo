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

from openerp.report import report_sxw
from openerp.tools.translate import _
import time


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "title_str" : self._title_str,
            "origin_str" : _("Origin"),
            "date_str" : _("Alteration Date"),
            "address_str" : _("Address"),
            "quantity_str" : _("Quantity"),
            "address_text" : self._address_text,
            "product_str" : _("Product"),
            "productnr_str" : _("Product Number"),
            "get_min_date" : self._get_min_date,
            "get_max_date" : self._get_max_date,
            "group_by_address" : self._group_by_address
        })        

          
    def _title_str(self):
        shop_names = set()
        for o in self.objects:
            shop_name = o.shop_id and o.shop_id.name or None
            if shop_name:
                shop_names.add(shop_name)        
        return _("Order Overview %s") % (" / ".join(sorted(shop_names)),) 
    
    def _address_text(self,address):        
        if address:            
            return address.address_header.replace("\n"," / ")                          
        return ""
    
    def _get_min_date(self):
        objs = self.objects
        min_date = min(objs.write_date)
        
        return min_date
    
    def _get_max_date(self):
        objs = self.objects
        max_date = max(objs.write_date)
        
        return max_date
    
    def _group_by_address(self):
        res = []
        addresses = {}
        
        for picking in self.objects:
            address = addresses.get(picking.address_id.id)
            if not address:
                lines = []
                for line in picking.move_lines:
                    lines.append(line)
                    
                #lines = [picking]
                delivery_code = time.strftime("%Y%m%d")
                if picking.address_id:
                    delivery_code+= str(picking.address_id.id)
                address = { "address" : picking.address_id, 
                            "delivery_code" : delivery_code,
                            "client_order_ref" : picking.sale_id and picking.sale_id.client_order_ref or "",
                            "lines" : lines
                }
                addresses[picking.address_id.id]=address
                res.append(address)
            else:
                lines = address.get("lines")
                for line in picking.move_lines:
                    lines.append(line)
        
        
        return res
    
    