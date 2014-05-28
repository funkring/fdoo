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

from prov import net_ipv4_get

import ipcalc
import crypt
import os

from at_base import geo
from at_base import util
from prov_router import prov_router_wlan

class creator(prov_router_wlan):
    
    def frequency_get(self,port):
        return self.frequency_channel_get(port)
            
    def default_mcsrate(self):
        return 15
      
    def dual_channel(self):
        return True
      
    def default_ipv4_lan(self):
        return ipcalc.Network("192.168.1.20",24)
   
    def default_ipv4_wan(self):
        return ipcalc.Network("0.0.0.0",24)
             
    def basic_mode(self):
        return None
            
    def subsystem_id(self):
        return None
    
    def default_client_pairwise(self):
        return "CCMP"
             
    def create(self):
        config = {}
        
        #get params
        is_ap = self.mode_type == "ap"
        is_station = self.mode_type == "client"
        is_bridge = self.wlan_iface == self.lan_iface
        wlan_ssid_hidden = self.wlan_port.wlan_ssid_hidden
        wlan_wds = self.wlan_port.wlan_wds
        lat = self.unit.address_id.lat or 0.0
        lon = self.unit.address_id.lon or 0.0
        distance=1600   
        auto_ack_timeout=True     
        
        #as default use 40 Mhz bandwidth
        ieee_mode="11naht40"
        if is_ap and self.dual_channel() and self.wlan_channel:
            if self.wlan_channel.expand_lower:
                ieee_mode="11naht40minus"
            else:
                ieee_mode="11naht40plus"
            
        
        clksel=1
        cwm_mode=is_ap and 2 or 1 #if it is an station use 1 for 20/40 autoselection
        
        if self.wlan_port:
            for dest in self.wlan_port.destination_ids:
                dest_address = dest.unit_id.address_id
                elat = dest_address.lat or 0.0
                elon = dest_address.lon or 0.0
                if elat and elon:
                    distance=round(max(geo.distancem((lon,lat), (elon,elat)),distance))
                    auto_ack_timeout=False
            
            if self.wlan_port.wlan_bandwidth==5:
                ieee_mode="11naht20"
                clksel=4
                cwm_mode=0
            elif self.wlan_port.wlan_bandwidth==10:
                ieee_mode="11naht20"
                clksel=2
                cwm_mode=0
            elif self.wlan_port.wlan_bandwidth==20:
                ieee_mode="11naht20"
                clksel=1     
                cwm_mode=0
        
        naht_repl = self.basic_mode()
        if naht_repl:
            ieee_mode=ieee_mode.replace("naht", naht_repl)
        
        min_ack=27
        max_ack=200
        ack_timeout=min(int(round(distance/150.0)+min_ack),max_ack)
        
        ssid = self.wlan_port.wlan_ssid
        psk = self.wlan_port.wlan_psk
        host = self.hostname
        txpower = self.wlan_port.wlan_txpower                
        olsr_service = self.olsr_service            
        admin_password = self.unit.password or self.default_password()
        admin_password = crypt.crypt(admin_password, "Vv")
        admin_user = self.unit.user or self.default_user()     
        subsystem_id = self.subsystem_id()
        client_pairwise = self.default_client_pairwise()
        
        config["aaa.1.br.devname"]="br0"
        config["aaa.1.devname"]="ath0"
        config["aaa.1.driver"]="madwifi"
        config["aaa.1.radius.auth.1.status"]="disabled"
        config["aaa.1.ssid"]=ssid
        config["aaa.1.status"]=is_ap
        config["aaa.1.wpa.1.pairwise"]="CCMP"
        config["aaa.1.wpa.key.1.mgmt"]="WPA-PSK"
        config["aaa.1.wpa.psk"]=psk
        config["aaa.1.wpa"]="1"
        config["aaa.status"]=is_ap
        config["bridge.1.devname"]="br0"
        config["bridge.1.fd"]="1"
        config["bridge.1.port.1.devname"]="eth0"
        config["bridge.1.port.1.prio"]="10"
        config["bridge.1.port.1.status"]="enabled"
        config["bridge.1.port.2.devname"]="ath0"
        config["bridge.1.port.2.prio"]="30"
        config["bridge.1.port.2.status"]="enabled"
        config["bridge.1.port.3.devname"]="eth1"
        config["bridge.1.port.3.prio"]="20"
        config["bridge.1.port.3.status"]="enabled"
        config["bridge.1.stp.status"]="disabled"
        config["bridge.status"]=is_bridge
        config["dhcpc.1.devname"]="br0"
        config["dhcpc.1.status"]="disabled"
        config["dhcpc.status"]="disabled"
        config["dhcpd.1.status"]="disabled"
        config["dhcpd.status"]="disabled"
        config["discovery.status"]=False
        config["dnsmasq.1.devname"]="eth0"
        config["dnsmasq.1.status"]="enabled"
        config["dnsmasq.status"]=False
        config["dyndns.status"]="disabled"
        config["ebtables.1.cmd"]="-t nat -A PREROUTING --in-interface ath0 -j arpnat --arpnat-target ACCEPT"
        config["ebtables.1.status"]=is_bridge and is_station and not wlan_wds
        config["ebtables.2.cmd"]="-t nat -A POSTROUTING --out-interface ath0 -j arpnat --arpnat-target ACCEPT"
        config["ebtables.2.status"]=is_bridge and is_station and not wlan_wds
        config["ebtables.3.cmd"]="-t broute -A BROUTING --protocol 0x888e --in-interface ath0 -j DROP"
        config["ebtables.3.status"]="enabled"
        config["ebtables.50.status"]="disabled"
        config["ebtables.51.status"]="disabled"
        config["ebtables.52.status"]="disabled"
        config["ebtables.status"]=is_bridge
        config["gui.language"]="en_US"
        config["httpd.https.status"]="disabled"
        config["httpd.port"]="80"
        config["httpd.session.timeout"]="900"
        config["httpd.status"]="enabled"
        config["igmpproxy.status"]="disabled"
        config["iptables.1.status"]="disabled"
        config["iptables.2.status"]="disabled"
        config["iptables.200.status"]="disabled"
        config["iptables.3.status"]="disabled"
        config["iptables.4.status"]="disabled"
        config["iptables.5.status"]="disabled"
        config["iptables.50.status"]="disabled"
        config["iptables.51.status"]="disabled"
        config["iptables.52.status"]="disabled"
        config["iptables.status"]="disabled"
        config["netconf.1.alias.1.status"]="disabled"
        config["netconf.1.alias.2.status"]="disabled"
        config["netconf.1.alias.3.status"]="disabled"
        config["netconf.1.alias.4.status"]="disabled"
        config["netconf.1.alias.5.status"]="disabled"
        config["netconf.1.alias.6.status"]="disabled"
        config["netconf.1.alias.7.status"]="disabled"
        config["netconf.1.alias.8.status"]="disabled"
        config["netconf.1.autoip.status"]="disabled"
        config["netconf.1.autoneg"]=True
        config["netconf.1.devname"]="eth0"
        config["netconf.1.duplex"]=True
        config["netconf.1.hwaddr.status"]="disabled"
        config["netconf.1.hwaddr"]=""
        config["netconf.1.ip"]=is_bridge and "0.0.0.0" or self.lan_ipv4
        config["netconf.1.mtu"]="1500"
        config["netconf.1.netmask"]=is_bridge and "255.255.255.0" or self.lan_ipv4.netmask()
        config["netconf.1.promisc"]="enabled"
        config["netconf.1.speed"]=100
        config["netconf.1.status"]="enabled"
        config["netconf.1.up"]="enabled"
        config["netconf.2.alias.1.status"]="disabled"
        config["netconf.2.alias.2.status"]="disabled"
        config["netconf.2.alias.3.status"]="disabled"
        config["netconf.2.alias.4.status"]="disabled"
        config["netconf.2.alias.5.status"]="disabled"
        config["netconf.2.alias.6.status"]="disabled"
        config["netconf.2.alias.7.status"]="disabled"
        config["netconf.2.alias.8.status"]="disabled"
        config["netconf.2.allmulti"]="enabled"
        config["netconf.2.autoip.status"]="disabled"
        config["netconf.2.devname"]="ath0"
        config["netconf.2.hwaddr.status"]="disabled"
        config["netconf.2.hwaddr"]=""
        config["netconf.2.ip"]=is_bridge and "0.0.0.0" or self.wan_ipv4
        config["netconf.2.mtu"]="1500"
        config["netconf.2.netmask"]=self.wan_ipv4.netmask()
        config["netconf.2.promisc"]="enabled"
        config["netconf.2.status"]="enabled"
        config["netconf.2.up"]="enabled"
        config["netconf.3.alias.1.status"]="disabled"
        config["netconf.3.alias.2.status"]="disabled"
        config["netconf.3.alias.3.status"]="disabled"
        config["netconf.3.alias.4.status"]="disabled"
        config["netconf.3.alias.5.status"]="disabled"
        config["netconf.3.alias.6.status"]="disabled"
        config["netconf.3.alias.7.status"]="disabled"
        config["netconf.3.alias.8.status"]="disabled"
        config["netconf.3.autoip.status"]="disabled"
        config["netconf.3.devname"]="br0"
        config["netconf.3.hwaddr.status"]="disabled"
        config["netconf.3.ip"]=self.lan_ipv4
        config["netconf.3.mtu"]="1500"
        config["netconf.3.netmask"]=self.lan_ipv4.netmask()
        config["netconf.3.status"]=is_bridge
        config["netconf.3.up"]="enabled"
        config["netconf.4.alias.1.status"]="disabled"
        config["netconf.4.alias.2.status"]="disabled"
        config["netconf.4.alias.3.status"]="disabled"
        config["netconf.4.alias.4.status"]="disabled"
        config["netconf.4.alias.5.status"]="disabled"
        config["netconf.4.alias.6.status"]="disabled"
        config["netconf.4.alias.7.status"]="disabled"
        config["netconf.4.alias.8.status"]="disabled"
        config["netconf.4.autoip.status"]="disabled"
        config["netconf.4.devname"]="eth1"
        config["netconf.4.hwaddr.status"]="disabled"
        config["netconf.4.ip"]="0.0.0.0"
        config["netconf.4.mtu"]="1500"  
        config["netconf.4.netmask"]="255.255.255.0"      
        config["netconf.4.up"]="enabled"
        config["netconf.5.autoip.status"]="disabled"
        config["netconf.5.devname"]="ath1"
        config["netconf.5.mtu"]="1500"
        config["netconf.6.status"]="disabled"
        config["netconf.status"]="enabled"
        config["netmode"]=is_bridge and "bridge" or "router"
        config["ntpclient.status"]="disabled"
        config["olsrd.status"]=olsr_service!=None and olsr_service.enabled
        config["ppp.1.status"]="disabled"
        config["ppp.status"]="disabled"
        config["pwdog.status"]="disabled"
        config["radio.1.ack.auto"]=auto_ack_timeout
        config["radio.1.ackdistance"]=distance
        config["radio.1.acktimeout"]=ack_timeout
        #begin - collecting frames
        config["radio.1.ampdu.bytes"]=50000
        config["radio.1.ampdu.frames"]=32
        config["radio.1.ampdu.status"]=True
        #end - collecting frames
        config["radio.1.antenna"]="4"
        config["radio.1.chanshift"]="0"
        config["radio.1.clksel"]=clksel
        config["radio.1.countrycode"]="40"
        config["radio.1.cwm.enable"]="0"
        config["radio.1.cwm.mode"]=cwm_mode
        config["radio.1.devname"]="ath0"
        config["radio.1.dfs.status"]="disabled"
        config["radio.1.forbiasauto"]="0"
        config["radio.1.frag"]="off"
        config["radio.1.freq"]=self.wlan_frequency or "0"
        config["radio.1.ieee_mode"]=ieee_mode
        config["radio.1.low_txpower_mode"]="disabled"
        config["radio.1.mcastrate"]=self.default_mcsrate()
        config["radio.1.mode"]=is_ap and "master" or "managed"
        config["radio.1.obey"]="disabled"
        config["radio.1.polling"]="enabled"
        config["radio.1.pollingnoack"]="0"
        config["radio.1.pollingpri"]=""
        config["radio.1.rate.auto"]="enabled"
        config["radio.1.rate.mcs"]=self.default_mcsrate()
        config["radio.1.reg_obey"]="disabled"
        config["radio.1.rts"]="off"
        config["radio.1.status"]="enabled"
        
        if subsystem_id:        
            config["radio.1.subsystemid"]=subsystem_id
            
        config["radio.1.thresh62a"]=""
        config["radio.1.thresh62b"]=""
        config["radio.1.thresh62g"]=""
        config["radio.1.txpower"]=txpower        
        config["radio.countrycode"]="40"
        config["radio.status"]="enabled"
        config["resolv.host.1.name"]=host
        config["resolv.host.1.status"]="enabled"
        config["resolv.nameserver.1.ip"]="127.0.0.1"
        config["resolv.nameserver.1.status"]=False
        config["resolv.nameserver.2.status"]=False
        config["resolv.status"]="enabled"
        config["route.1.devname"]="br0"
        config["route.1.gateway"]="0.0.0.0"
        config["route.1.ip"]="0.0.0.0"
        config["route.1.netmask"]="0"
        config["route.1.status"]=False
        config["route.status"]="enabled"
        config["snmp.status"]="disabled"
        config["sshd.port"]="22"
        config["sshd.status"]="enabled"
        config["syslog.remote.status"]=""
        config["syslog.status"]="disabled"
        config["system.button.reset"]="enabled"
        config["system.date.status"]="disabled"
        config["system.date"]=""
        config["system.eirp.status"]="enabled"
        if lat and lon:
            config["system.latitude"]=lat
            config["system.longitude"]=lon
        config["system.modules.blacklist.1.status"]="disabled"
        config["system.modules.blacklist.2.status"]="disabled"
        config["system.modules.blacklist.3.status"]="disabled"
        config["system.modules.blacklist.4.status"]="disabled"
        config["system.modules.blacklist.status"]="disabled"
        config["system.timezone"]="GMT-1"
        config["telnetd.status"]="disabled"
        config["tshaper.in.1.devname"]="eth0"
        config["tshaper.out.1.devname"]="ath0"
        config["tshaper.status"]="disabled"
        config["users.1.name"]=admin_user
        config["users.1.password"]=admin_password
        config["users.1.status"]="enabled"
        config["users.2.status"]="disabled"
        config["users.status"]="enabled"
        config["vlan.1.status"]="disabled"
        config["vlan.2.status"]="disabled"
        config["vlan.status"]="disabled"
        config["wireless.1.addmtikie"]="enabled"
        config["wireless.1.ap"]=""
        config["wireless.1.authmode"]="1"
        config["wireless.1.autowds"]="disabled"
        config["wireless.1.compression"]="0"        
        config["wireless.1.devname"]="ath0"
        config["wireless.1.fastframes"]="0"
        config["wireless.1.frameburst"]="0"
        config["wireless.1.hide_ssid"]=(is_ap and wlan_ssid_hidden)
        config["wireless.1.l2_isolation"]="disabled"
        config["wireless.1.mac_acl.1.mac"]=""
        config["wireless.1.mac_acl.1.status"]="disabled"
        config["wireless.1.mac_acl.10.mac"]=""
        config["wireless.1.mac_acl.10.status"]="disabled"
        config["wireless.1.mac_acl.11.mac"]=""
        config["wireless.1.mac_acl.11.status"]="disabled"
        config["wireless.1.mac_acl.12.mac"]=""
        config["wireless.1.mac_acl.12.status"]="disabled"
        config["wireless.1.mac_acl.13.mac"]=""
        config["wireless.1.mac_acl.13.status"]="disabled"
        config["wireless.1.mac_acl.14.mac"]=""
        config["wireless.1.mac_acl.14.status"]="disabled"
        config["wireless.1.mac_acl.15.mac"]=""
        config["wireless.1.mac_acl.15.status"]="disabled"
        config["wireless.1.mac_acl.16.mac"]=""
        config["wireless.1.mac_acl.16.status"]="disabled"
        config["wireless.1.mac_acl.17.mac"]=""
        config["wireless.1.mac_acl.17.status"]="disabled"
        config["wireless.1.mac_acl.18.mac"]=""
        config["wireless.1.mac_acl.18.status"]="disabled"
        config["wireless.1.mac_acl.19.mac"]=""
        config["wireless.1.mac_acl.19.status"]="disabled"
        config["wireless.1.mac_acl.2.mac"]=""
        config["wireless.1.mac_acl.2.status"]="disabled"
        config["wireless.1.mac_acl.20.mac"]=""
        config["wireless.1.mac_acl.20.status"]="disabled"
        config["wireless.1.mac_acl.21.mac"]=""
        config["wireless.1.mac_acl.21.status"]="disabled"
        config["wireless.1.mac_acl.22.mac"]=""
        config["wireless.1.mac_acl.22.status"]="disabled"
        config["wireless.1.mac_acl.23.mac"]=""
        config["wireless.1.mac_acl.23.status"]="disabled"
        config["wireless.1.mac_acl.24.mac"]=""
        config["wireless.1.mac_acl.24.status"]="disabled"
        config["wireless.1.mac_acl.25.mac"]=""
        config["wireless.1.mac_acl.25.status"]="disabled"
        config["wireless.1.mac_acl.26.mac"]=""
        config["wireless.1.mac_acl.26.status"]="disabled"
        config["wireless.1.mac_acl.27.mac"]=""
        config["wireless.1.mac_acl.27.status"]="disabled"
        config["wireless.1.mac_acl.28.mac"]=""
        config["wireless.1.mac_acl.28.status"]="disabled"
        config["wireless.1.mac_acl.29.mac"]=""
        config["wireless.1.mac_acl.29.status"]="disabled"
        config["wireless.1.mac_acl.3.mac"]=""
        config["wireless.1.mac_acl.3.status"]="disabled"
        config["wireless.1.mac_acl.30.mac"]=""
        config["wireless.1.mac_acl.30.status"]="disabled"
        config["wireless.1.mac_acl.31.mac"]=""
        config["wireless.1.mac_acl.31.status"]="disabled"
        config["wireless.1.mac_acl.32.mac"]=""
        config["wireless.1.mac_acl.32.status"]="disabled"
        config["wireless.1.mac_acl.4.mac"]=""
        config["wireless.1.mac_acl.4.status"]="disabled"
        config["wireless.1.mac_acl.5.mac"]=""
        config["wireless.1.mac_acl.5.status"]="disabled"
        config["wireless.1.mac_acl.6.mac"]=""
        config["wireless.1.mac_acl.6.status"]="disabled"
        config["wireless.1.mac_acl.7.mac"]=""
        config["wireless.1.mac_acl.7.status"]="disabled"
        config["wireless.1.mac_acl.8.mac"]=""
        config["wireless.1.mac_acl.8.status"]="disabled"
        config["wireless.1.mac_acl.9.mac"]=""
        config["wireless.1.mac_acl.9.status"]="disabled"
        config["wireless.1.mac_acl.policy"]="allow"
        config["wireless.1.mac_acl.status"]="disabled"
        config["wireless.1.macclone"]="disabled"
        config["wireless.1.scan_list.channels"]=""
        config["wireless.1.scan_list.status"]="disabled"
        config["wireless.1.security"]="none"
        config["wireless.1.sens"]=0
        config["wireless.1.signal_led1"]=94
        config["wireless.1.signal_led2"]=80
        config["wireless.1.signal_led3"]=73
        config["wireless.1.signal_led4"]=65
        config["wireless.1.ssid"]=ssid
        config["wireless.1.status"]="enabled"
        config["wireless.1.wds.1.peer"]=""
        config["wireless.1.wds.2.peer"]=""
        config["wireless.1.wds.3.peer"]=""
        config["wireless.1.wds.4.peer"]=""
        config["wireless.1.wds.5.peer"]=""
        config["wireless.1.wds.6.peer"]=""
        config["wireless.1.wds"]=wlan_wds
        config["wireless.1.wmm"]="enabled"
        config["wireless.1.wmmlevel"]=""
        config["wireless.status"]="enabled"
        config["wpasupplicant.device.1.devname"]="ath0"
        config["wpasupplicant.device.1.driver"]="madwifi"
        config["wpasupplicant.device.1.profile"]="WPA-PSK"
        config["wpasupplicant.device.1.status"]=is_station
        config["wpasupplicant.profile.1.name"]="WPA-PSK"
        config["wpasupplicant.profile.1.network.1.bssid"]=""
        config["wpasupplicant.profile.1.network.1.eap.1.status"]="disabled"
        config["wpasupplicant.profile.1.network.1.key_mgmt.1.name"]="WPA-PSK"
        config["wpasupplicant.profile.1.network.1.pairwise.1.name"]=client_pairwise
        config["wpasupplicant.profile.1.network.1.proto.1.name"]="WPA"
        config["wpasupplicant.profile.1.network.1.psk"]=psk
        config["wpasupplicant.profile.1.network.1.ssid"]=ssid
        config["wpasupplicant.status"]=is_station
        config["update.check.status"]="disabled"

        cfg_file = os.path.join(self.build_dir,"xm.cfg")
        util.writeProperties(cfg_file, config, bool_true="enabled", bool_false="disabled")
        
        etc_dir = os.path.join(self.build_dir,"etc/persistent")
        os.makedirs(etc_dir) 
               
        if olsr_service:        
            olsr_cfg_file = open(os.path.join(etc_dir,"olsrd.conf"),"w")        
            olsr_cfg_file.write(self.olsr_config_txt())
            olsr_cfg_file.write("\n")        
            olsr_cfg_file.write(self.olsr_config_txt("olsrd_txtinfo.so.0.1"))
            olsr_cfg_file.write("\n")   
            olsr_cfg_file.write('Hna4\n{\n')
            for iface in self.unit.iface_ids:
                hna_net = iface.network_id and iface.network_id.parent_id or None
                if hna_net and hna_net.published and iface.type!="gw" and not hna_net.private:
                    hna_ip = net_ipv4_get(hna_net)                
                    if hna_ip:
                        olsr_cfg_file.write('    %s %s\n' % (hna_ip,hna_ip.netmask()))
            olsr_cfg_file.write('}\n\n')   
            olsr_cfg_file.write(self.olsr_config_txt("InterfaceDefaults"))
            olsr_cfg_file.write("\n")                        
            for iface in olsr_service.iface_ids:
                if iface.code:
                    iface_mode="ether"
                    if not is_bridge and iface==self.wlan_iface:
                        iface_mode="mesh"                        
                    olsr_cfg_file.write('''
Interface "%s" {
        Mode "%s"
}                

''' % (iface.code,iface_mode))
            
            olsr_cfg_file.close()
                
        

        