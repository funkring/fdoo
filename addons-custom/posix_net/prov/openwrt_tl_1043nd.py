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

import openwrt_airrouter 

class creator(openwrt_airrouter.creator):

    def wlan_header_get(self):
        return """config wifi-device  radio0
    option type     mac80211
    option channel  %s
    option hwmode   11ng
    option htmode   HT20
    #option macaddr  00:00:00:00:00:00
    list ht_capab   SHORT-GI-40    
    list ht_capab   DSSS_CCK-40
""" % (self.wlan_frequency or "auto",)

    def switch_header_get(self):
        return """config switch
    option name 'rtl8366rb'
    option reset '1'     
    option enable_vlan '1'     
                                      
config switch_vlan
    option device 'rtl8366rb'
    option vlan '1'       
    option ports '1 2 3 4 5t'
 
config switch_vlan
    option device 'rtl8366rb'
    option vlan '2' 
    option ports '0 5t' 

"""
