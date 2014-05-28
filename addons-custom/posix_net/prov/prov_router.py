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

import prov
import ipcalc
from openerp.osv import osv
from openerp.tools.translate import _

class prov_router(prov.prov_creator):
    pass


class prov_router_wlan(prov.prov_creator):
   
    def channel_get(self,port):
        channel = None
        if port.wlan_available:
            channel = (port and port.wlan_channel_id) or None
        
        port_type = port.type_id      
        if channel and port_type:
            channel = self.pool.get("posix_net.frequency_mapping_line").mapping_channel_get(self.cr,self.uid,port.wlan_bandwidth,channel,
                                                                          port_type.id,shifting=port.wlan_shifting)
        return channel
                   
    def frequency_name_get(self,port):
        channel = self.channel_get(port)                                
        return channel and channel.name or None
    
    def frequency_channel_get(self,port):
        channel = self.channel_get(port)            
        return channel and channel.channel or None
                   
    def frequency_get(self,port):
        return self.frequency_name_get(port)
   
    def default_ipv4_lan(self):
        return ipcalc.Network("192.168.1.1",24)
   
    def default_ipv4_wan(self):
        return None
     
    def default_ipv6_lan(self):
        return None
    
    def default_ipv6_wan(self):
        return None

    def needs_iface_code(self):
        return False
    
    def needs_mode(self):
        return True
    
    def prepare(self):
        self.gateway_iface=None
        self.wlan_iface=None        
        self.wlan_port=None
        self.wlan_frequency=None
        self.wlan_channel=None
        self.lan_iface=None
        self.wan_iface=None
        self.mode_type=None
        self.olsr_service=None        
        self.dns_service=None
        
        self.lan_ipv4 = self.default_ipv4_lan()                
        self.lan_ipv6 = self.default_ipv6_lan()                
        self.wan_ipv4 = self.default_ipv4_wan()
        self.wan_ipv6 = self.default_ipv6_wan()
        
        #inspect ports     
        for iface in self.unit.iface_ids: 
            if self.needs_iface_code() and not iface.code:
                raise osv.except_osv(_("Error !"), _("Interface %s from device %s has no valid code") % (iface.name,self.unit.name))
                
            for port in iface.port_ids:
                if port.wlan_available and port.enabled:
                    self.wlan_iface=iface
                    self.wlan_port=port
                    self.wlan_frequency=self.frequency_get(port)
                    self.wlan_channel=self.channel_get(port)
                    self.mode_type=port.mode_type
                    if not port.wlan_ssid:
                        raise osv.except_osv(_("Error !"), _("Port %s from device %s has no valid ssid") % (port.name,self.unit.name))
                    if port.wlan_auth_mode=="psk" and not port.wlan_psk or len(port.wlan_psk) < 8:
                        raise osv.except_osv(_("Error !"), _("WLAN Key of port %s form device %s must be creater than seven characters") % (port.name,self.unit.name))
                        
                    
            if iface.type == "gw" or iface.type == "link":
                if iface.type == "gw":
                    self.gateway_iface=iface
                self.wan_iface = iface
            elif iface.type == "site":
                self.lan_iface = iface
                  
        #check for services
        for service in self.unit.service_ids:
            if service.type_id.name=="olsr":        
                self.olsr_service=service                
            elif service.type_id.name=="dns":
                self.dns_service=service
                
       
        #get ip from interfaces
        if self.lan_iface:
            if self.lan_iface.ipv4_ip and self.lan_iface.ipv4_mask:
                self.lan_ipv4 = ipcalc.Network(self.lan_iface.ipv4_ip,self.lan_iface.ipv4_mask,version=4)
            if self.lan_iface.ipv6_ip and self.lan_iface.ipv6_mask:
                self.lan_ipv6 = ipcalc.Network(self.lan_iface.ipv6_ip,self.lan_iface.ipv6_mask,version=6)       
        if self.wan_iface:
            if self.wan_iface.ipv4_ip and self.wan_iface.ipv4_mask:
                self.wan_ipv4 = ipcalc.Network(self.wan_iface.ipv4_ip,self.wan_iface.ipv4_mask,version=4)
            if self.wan_iface.ipv6_ip and self.wan_iface.ipv6_mask:
                self.wan_ipv6 = ipcalc.Network(self.wan_iface.ipv6_ip,self.wan_iface.ipv6_mask,version=6)
     
        if self.needs_mode() and self.wlan_port and not (self.mode_type and self.mode_type in ["client","ap"]  ):
            raise osv.except_osv(_("Error !"), _("There is no valid wlan interface in ap or client mode for device %s") % (self.unit.name,))    
        return True
            
            