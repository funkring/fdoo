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
from openerp.addons.at_base import util

class mapping_channel_wizard(osv.osv_memory):
    
    def create_channels(self,cr,uid,wizard,channels,context=None):        
        mapping_line = self.pool.get("posix_net.frequency_mapping_line")
                             
        for channel in channels:
            mapping_ids = mapping_line.search(cr,uid,[("frequency_mapping_id","=",wizard.id),
                                                      ("channel","=",channel.channel),
                                                      ("bandwidth","=",wizard.bandwidth),
                                                      ("shifting","=",wizard.shifting)])
            if mapping_ids:
                mapping_line.unlink(cr,uid,mapping_ids)
            
            mapping_line.create(cr,uid,{
                        "frequency_mapping_id" : wizard.mapping_id.id,
                        "channel" : channel.channel,
                        "name" : wizard.mapping,
                        "bandwidth" : wizard.bandwidth,
                        "shifting": wizard.shifting                            
                    },context)
    
    def create_mappings(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            self.create_channels(cr, uid, obj, obj.channel_ids)
        return { "type" : "ir.actions.act_window_close" }
            
      
    def _default_mapping_id_get(self, cr, uid, context=None):
        data = util.data_get(context)
        if data and data["model"]=="posix_net.frequency_mapping":
            return data["id"]                    
        return None
        
      
    _name = "posix_net.frequency_mapping_channel_wizard"
    _description = "Mapping Channel Wizard"    
    _columns = {
        "mapping_id" : fields.many2one("posix_net.frequency_mapping","Frequency Mapping",required=True),
        "mapping" : fields.char("Mapping",size=16,required=True),        
        "bandwidth" : fields.integer("Bandwidth",required=True),        
        "shifting" : fields.boolean("Shifting"),
        "channel_ids" : fields.many2many("posix_net.wlan_channel", "frequency_mapping_channel_rel", "wizard_id", "channel_id", string="Channels"),
    }
    
    _defaults = {
        "mapping_id" : _default_mapping_id_get 
    }
