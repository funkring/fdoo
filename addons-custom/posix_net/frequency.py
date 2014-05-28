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

class posix_net_wlan_channel(osv.osv):
    
    _name="posix_net.wlan_channel"
    _description="WLAN Channels"
    _order = "frequency asc"
    
    def name_get(self, cr, uid, ids, context=None):             
        
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ["name", "frequency"], context=context)
        res = []
        for record in reads:
           
            name = record["name"]
            if record["frequency"]:
                complete_name = str(record["frequency"]) + " / " + name
            res.append((record["id"], complete_name))
        return res
    
    def _get_preferred_channel_id(self,cr,uid, allowed_channel_ids, used_ids,context=None):        
        channel_ranges = []    
        search_value = []    
        if allowed_channel_ids:
            search_value.append(("id", "in", [x.id for x in allowed_channel_ids]))
        channels = self.browse(cr,uid,self.search(cr, uid, search_value))
        if channels:
            if not used_ids:
                return channels[0].id
            used_channels = self.browse(cr, uid, used_ids)
            max_range = channels[-1].frequency - channels[0].frequency 
            for channel in channels:
                r = max_range
                for used in used_channels:
                    r = min(abs(channel.frequency-used.frequency),r)
                channel_ranges.append((r,channel.id))
                
        if channel_ranges:
            channel_ranges.sort(reverse=True)            
            if channel_ranges[0][0]:
                return channel_ranges[0][1]
        return None 
    
    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)
    
    def _is_highest(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id]=(self.search(cr, uid, [], limit=1, order="frequency desc")[0]==obj.id)        
        return res
    
    def _is_lowest(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id]=(self.search(cr, uid, [], limit=1, order="frequency asc")[0]==obj.id)        
        return res
    _columns = {
        "name" : fields.char("Channel", size=128, required=True, select=True),
        "frequency" : fields.integer("Frequency"),
        "is_highest" : fields.function(_is_highest,"Highest",method=True, type='boolean',string="Highest Channel"),
        "is_lowest" : fields.function(_is_lowest,"Lowest",method=True, type='boolean',string="Lowest Channel"),
        "expand_lower" : fields.boolean("Expand To Lower"),
        "complete_name": fields.function(_name_get_fnc, method=True, type="char", size=256, string="Name", store=True, select=True),
    }
    
