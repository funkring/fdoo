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

from openerp.osv import fields, osv
from openerp.tools.translate import _

class connection_wizard(osv.TransientModel):
    _name = "posix_net.connection_wizard"
    _description = "Connection between units"
    
    def do_connect(self, cr, uid, ids, context=None):
        unit_obj = self.pool.get("posix_net.unit")
        iface_obj = self.pool.get("posix_net.iface")
        port_obj = self.pool.get("posix_net.port")
        ipv4_obj = self.pool.get("posix_net.net_ipv4_address")
        for wizard in self.browse(cr, uid, ids):
            local_port = wizard.local_port_id
            target_unit = wizard.target_unit_id
            target_port = wizard.target_port_id
            if local_port and not target_unit and not target_port:
                if local_port.iface_id:
                    ipv4_obj.unlink(cr, uid, local_port.iface_id.ipv4_address_id and local_port.iface_id.ipv4_address_id.id or None)
                    iface_obj.write(cr, uid, local_port.iface_id.id, {"parent_id" : None, "ipv4_address_id" : None})
                port_obj.write(cr, uid, local_port.id, {"linked_port_id" : None})
            elif target_port:
                if local_port.iface_id:
                    ipv4_obj.unlink(cr, uid, local_port.iface_id.ipv4_address_id and local_port.iface_id.ipv4_address_id.id or None)
                    iface_obj.write(cr, uid, local_port.iface_id.id, {"parent_id" : target_port.iface_id.parent_id.id, "ipv4_address_id" : None})
                port_obj.write(cr, uid, local_port.id, {"linked_port_id" : target_port.id})
                unit_obj.do_validate(cr, uid, [local_port.unit_id.id])
            else:
                raise osv.except_osv(_("Error"), _("The fields must be correctly set!"))
            
            self.unlink(cr, uid, wizard.id, context)
            
    def onchange_unit(self, cr, uid, ids, unit_id, context=None):
        res = {
            "value" : {}
        }
        if unit_id:
            unit_obj = self.pool.get("posix_net.unit")
            unit = unit_obj.browse(cr, uid, unit_id, context)
            port_list = []
            link_list = []
            link_unit_list = []
            for port in unit.port_ids:
                if port.mode == "client":
                    port_list.append(port.id)
                    for link in port.possible_link_port_ids:
                        if link.mode == "ap":
                            link_list.append(link.id)
                            link_unit_list.append(link.unit_id.id)
            res["value"]["possible_unit_ids"] = link_unit_list
            res["value"]["possible_port_ids"] = link_list
            if len(port_list) == 1:
                res["value"]["local_port_id"]=port_list[0]
            else:
                res["value"]["local_port_id"] = None
        else:
            res["value"]["local_port_id"] = None
            res["value"]["target_port_id"] = None
            res["value"]["target_unit_id"] = None
            res["value"]["possible_unit_ids"] = None
            res["value"]["possible_port_ids"] = None
        return res
            
    def onchange_local_port(self, cr, uid, ids, local_port_id, target_unit_id, unit_id, context=None):
        res = {
            "value" : {}
        }
        if local_port_id:
            port_obj = self.pool.get("posix_net.port") 
            local_port = port_obj.browse(cr, uid, local_port_id)
            
            possible_links = local_port.possible_link_port_ids
            port_list = []
            unit_list = []
            for link in possible_links:
                port_list.append(link.id)
                unit_list.append(link.unit_id.id)
            if target_unit_id not in unit_list:
                res["value"]["target_unit_id"] = None
            res["value"]["possible_unit_ids"] = unit_list
            if not target_unit_id:
                res["value"]["possible_port_ids"] = port_list
        return res
    
    def onchange_target_unit(self, cr, uid, ids, target_unit_id, local_port_id, unit_id, context=None):
        res = {
            "value" : {}
        }
        unit_obj = self.pool.get("posix_net.unit")
        if target_unit_id:
            unit = unit_obj.browse(cr, uid, target_unit_id, context)
            port_list = []
            
            for port in unit.port_ids:
                if port.mode == "ap":
                    port_list.append(port.id)
            res["value"]["possible_port_ids"] = port_list
            res["value"]["target_port_id"] = port_list[0]
            
            
        elif local_port_id:
            port_obj = self.pool.get("posix_net.port")
            local_port = port_obj.browse(cr, uid, local_port_id, context)
            possible_links = local_port.possible_link_port_ids
            port_list = []
            unit_list = []
            for link in possible_links:
                port_list.append(link.id)
                unit_list.append(link.unit_id.id)
            res["value"]["possible_port_ids"] = port_list
            res["value"]["possible_unit_ids"] = unit_list
            res["value"]["target_port_id"] = None
            
        elif unit_id:
            unit_list = []
            port_list = []
            unit = unit_obj.browse(cr, uid, unit_id)
            for port in unit.port_ids:
                if port.mode == "client":
                    for link_port in port.possible_link_port_ids:
                        if link_port.mode == "ap" and link_port.id not in res:
                            port_list.append(link_port.id)
                            unit_list.append(link_port.unit_id.id)
            res["value"]["possible_port_ids"] = port_list
            res["value"]["possible_unit_ids"] = unit_list
            res["value"]["target_port_id"] = None
        return res
    
    def onchange_target_port(self, cr, uid, ids, target_port_id, local_port_id, context=None):
        res = {
            "value" : {}
        }
        if target_port_id:
            port = self.pool.get("posix_net.port").browse(cr, uid, target_port_id)
            res["value"]["target_unit_id"] = port.unit_id.id
            
        return res
    
    def _current_unit_id(self, cr, uid, context=None):
        if context.get("active_id"):
            return context.get("active_id")
    
    def _possible_unit_ids(self, cr, uid, context=None):
        res = []
        if context.get("active_id"):
            unit_obj = self.pool.get("posix_net.unit")
            unit = unit_obj.browse(cr, uid, context.get("active_id"))
            for port in unit.port_ids:
                if port.mode == "client":
                    for link_port in port.possible_link_port_ids:
                        if link_port.mode == "ap" and link_port.unit_id.id not in res:
                            res.append(link_port.unit_id.id)
        return res
    
    def _possible_port_ids(self, cr, uid, context=None):
        res = []
        if context.get("active_id"):
            unit_obj = self.pool.get("posix_net.unit")
            unit = unit_obj.browse(cr, uid, context.get("active_id"))
            for port in unit.port_ids:
                if port.mode == "client":
                    for link_port in port.possible_link_port_ids:
                        if link_port.mode == "ap" and link_port.id not in res:
                            res.append(link_port.id)
        return res
    
    def _local_port_id(self, cr, uid, context=None):
        if context.get("active_id"):
            unit_obj = self.pool.get("posix_net.unit")
            unit = unit_obj.browse(cr, uid, context.get("active_id"))
            possible_ports = []
            for port in unit.port_ids:
                if port.mode == "client":
                    possible_ports.append(port.id)
        if len(possible_ports) == 1:
            return possible_ports[0]
            
    
    _columns = {
        "local_port_id" : fields.many2one("posix_net.port", "Local port", required=True),
        "target_unit_id" : fields.many2one("posix_net.unit", "Target unit"),
        "target_port_id" : fields.many2one("posix_net.port", "Target port"),
        "possible_unit_ids" : fields.many2many("posix_net.unit", "posix_unit_connection_rel", "wizard_id", "unit_id", "Possible units"),
        "possible_port_ids" : fields.many2many("posix_net.port", "posix_port_connection_rel", "wizard_id", "port_id", "Possible ports"),
        "unit_id" : fields.many2one("posix_net.unit", "Unit", required=True)
    }
    
    _defaults = {
        "unit_id" : _current_unit_id,
        "possible_unit_ids" : _possible_unit_ids,
        "possible_port_ids" : _possible_port_ids,
        "local_port_id" : _local_port_id,
    }