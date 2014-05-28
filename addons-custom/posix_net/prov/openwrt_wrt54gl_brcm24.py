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

from posix_net.prov import openwrt_airrouter

class creator(openwrt_airrouter.creator):
    
    def wlan_device_get(self):
        return "wl0"
    
    def needs_iface_code(self):
        return True
        
    def switch_header_get(self):
        return """## VLAN configuration            
config switch eth0
        option enable   1

config switch_vlan eth0_0
        option device   "eth0"
        option vlan     0
        option ports    "0 1 2 3 5"

config switch_vlan eth0_1
        option device   "eth0"
        option vlan     1
        option ports    "4 5"
        
"""
 
    def wlan_header_get(self):
        return """config wifi-device  wl0
    option type     broadcom
    option country  'AT'
    option distance  2000
    option channel  %s
""" % (self.wlan_frequency or "7",)

    def firewall_header_get(self):
        return """config defaults                                 
    option syn_flood        1               
    option input            ACCEPT          
    option output           ACCEPT          
    option forward          REJECT
"""
        