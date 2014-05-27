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

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "address_lines" : self._address_lines,
            "delivery_address_lines" : self._delivery_address_lines
        })

    def _address_lines(self,purchase):
        partner = purchase.partner_id or None
        if partner:
            partner_obj = self.pool.get("res.partner")
            return partner_obj._build_address_text(self.cr, self.uid, partner) 
        return []  
    
    def _delivery_address_lines(self,purchase):
        partner = purchase.dest_address_id or (purchase.warehouse_id and purchase.warehouse_id.partner_id) or None
        if partner:
            partner_obj = self.pool.get("res.partner")
            return partner_obj._build_address_text(self.cr, self.uid, partner)
        elif purchase.warehouse_id:
            return [purchase.warehouse_id.name]        
        return []  
    
    