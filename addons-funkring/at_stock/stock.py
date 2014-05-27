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

from openerp.osv import fields,osv
from openerp.addons.at_base import util
from dateutil.relativedelta import relativedelta

class stock_picking(osv.osv):
    
    def _location_partner_id(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids)
        for picking in self.browse(cr, uid, ids, context):
            partner = None
            purchase = picking.purchase_id
            
            #partner from purchase
            if purchase:
                #purchase destination
                partner = purchase.dest_address_id
                if not partner:
                    # or location destination
                    location = purchase.location_id
                    if location: 
                        partner = location.partner_id
                        # take partner from parent locations
                        while not partner:
                            location = location.partner_id
                            if not location:
                                break
                            partner = location.partner_id
            
            #take default partner from company            
            if not partner:
                partner =  picking.company_id.partner_id
              
            #set partner if found
            if partner:
                res[picking.id] = partner.id
        return res
    
    _inherit = "stock.picking"
    _columns = {
        "location_partner_id" : fields.function(_location_partner_id, string="Location Partner", type="many2one", obj="res.partner", store=False)
    }
    

class stock_move(osv.osv):
    
    def _update_expected_date(self,cr,uid,moves,context=None):
        picking_obj = self.pool.get("stock.picking")
        for move in moves:
            orig_move = move            
            move_dest = move.move_dest_id
            delay = orig_move.location_id and orig_move.location_id.chained_delay or 0
            while move_dest:
                orig_expected_date = self.read(cr, uid, orig_move.id, ["date_expected"], context)["date_expected"]
                dest_expected_date = self.read(cr, uid, move_dest.id, ["date_expected"], context)["date_expected"]
                expected_date = util.mergeTimeStr(util.strToTime(orig_expected_date)+relativedelta(days=delay),dest_expected_date)                
                #
                if dest_expected_date != expected_date:
                    vals = { "date_expected" : expected_date }
                    # write over picking id 
                    # to update stored functions
                    if move_dest.picking_id:
                        picking_obj.write(cr, uid, move_dest.picking_id.id, { "move_lines" : [(1,move_dest.id,vals)] }, context)
                    else:
                        self.write(cr, uid, [move_dest.id], vals, context)
                    
                #
                orig_move = move_dest
                move_dest = orig_move.move_dest_id
                delay = orig_move.location_id and orig_move.location_id.chained_delay or 0
    
    def create_chained_picking(self, cr, uid, moves, context=None):
        new_moves = super(stock_move, self).create_chained_picking(cr, uid, moves, context=context)
        self._update_expected_date(cr, uid, moves, context)        
        return new_moves
    
    _inherit = "stock.move"
