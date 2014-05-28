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

from prov import iface_ipv4_get
from prov import net_ipv4_get
import prov_router
import os
import ipcalc
from openerp.addons.at_base import util
from openerp.osv import osv
from openerp.tools.translate import _

class creator(prov_router.prov_router_wlan):
    
    def wlan_device_get(self):
        return "radio0"
        
    def needs_iface_code(self):
        return True
    
    def image_builder_name(self):
        return "OpenWrt-ImageBuilder-ar71xx-for-Linux"
    
    def image_builder_profile(self):
        return "UBNT"    
    
    def image_builder_packages(self):
        return []
       
    def use_bridge_name_as_iface(self):
        return False
       
    def switch_header_get(self):
        return """config switch
    option name 'eth0'
    option reset '1'
    option enable_vlan '1'
 
config switch_vlan
    option device 'eth0'
    option vlan '1'
    option ports '0 1 2 3 4'

"""

    def wlan_header_get(self):
        return """config wifi-device  radio0
    option type     mac80211
    option channel  %s
    option hwmode   11ng
    option htmode   HT20
    #option macaddr  00:00:00:00:00:00
    list ht_capab   SHORT-GI-40
    list ht_capab   TX-STBC
    list ht_capab   RX-STBC1
    list ht_capab   DSSS_CCK-40
""" % (self.wlan_frequency or "auto",)
   
    def firewall_header_get(self):
        return """config defaults                                 
    option syn_flood        1               
    option input            ACCEPT          
    option output           ACCEPT          
    option forward          REJECT              
    option disable_ipv6     1     
"""
        
    def create(self):
        
        #############################################################
        # creation prepare
        #############################################################
        
        for service in self.unit.service_ids:
            if service.type_id:
                key = ("%s.enabled") % service.type_id.name
                if not self.properties.has_key(key):
                    self.properties[key]=service.enabled
        
        has_olsr = self.olsr_service and self.olsr_service.enabled
        olsr_dns_ip4 = []     
        bridged_iface_ids = []
        
        etc_dir = os.path.join(self.build_dir,"etc")
        init_dir = os.path.join(self.build_dir,"etc/init.d")
        cfg_dir = os.path.join(self.build_dir,"etc/config")        
        os.makedirs(init_dir)
        os.makedirs(cfg_dir) 
        
        #############################################################
        # write system configuration
        #############################################################
        
        sysf = open(os.path.join(cfg_dir,"system"),"w")
        sysf.write("""config system
    option hostname '%s'
    option zonename 'Europe/Vienna'
    option timezone 'CET-1CEST,M3.5.0,M10.5.0/3'

config timeserver
    list server     0.openwrt.pool.ntp.org
    list server     1.openwrt.pool.ntp.org
    list server     2.openwrt.pool.ntp.org
    list server     3.openwrt.pool.ntp.org

""" % (self.unit.name))                
        sysf.close()
        
         
        #############################################################
        # write VTUN Configuration
        #############################################################
        
        vtun_start = []
        vtunf = None
        
        for port in self.unit.port_ids:
            if port.tunnel_available:
                port_type = port.type_id                
                if port_type and port_type.tunnel_type=="vtun":
                    if not vtunf:
                        vtunf = open(os.path.join(etc_dir,"vtund.conf"),"w")                        
                        vtunf.write(self.vtun_config_txt("options"))
                        vtunf.write("\n")
                        vtunf.write(self.vtun_config_txt("default"))
                        vtunf.write("\n")                        
                    
                    iface = port.iface_id
                    if iface:    
                        bridge_name = None                   
                        if port.mode_type == "ap":
                            bridge_name = "br-%s" % (iface.name,)
                            vtunf.write(self.vtun_tunnel_txt(port.tunnel_name, port.tunnel_password,
                                                             multi=True, bridge=bridge_name))
                            vtunf.write("\n")
                            bridged_iface_ids.append(iface.id)
                            #                            
                            vtun_start.append("vtund -s")
                        elif port.mode_type == "client":
                            bridge_name = "br-%s" % (iface.name,)
                            vtunf.write(self.vtun_tunnel_txt(port.tunnel_name, 
                                                             port.tunnel_password,bridge=bridge_name))
                            vtunf.write("\n")
                            bridged_iface_ids.append(iface.id)
                            #
                            phy_iface = port.tunnel_phyiface_id
                            linked_ipv4 = iface_ipv4_get(phy_iface) 
                            if linked_ipv4:                                
                                vtun_start.append("vtund %s %s" % (port.tunnel_name,linked_ipv4))
                                
                        if bridge_name:
                            if not self.use_bridge_name_as_iface() and not iface.code.startswith("eth"):
                                raise osv.except_osv("Error !", "Must be an eth iface for tunnel (for example ethx.10) on %s/%s!" % (iface.name,self.unit.name))
                            elif self.use_bridge_name_as_iface() and not iface.code.startswith("br-"):
                                raise osv.except_osv("Error !", "Must be an br- iface for tunnel (for example br-guest) on %s/%s!" % (iface.name,self.unit.name))
                            if iface.code.endswith(".1"):
                                raise osv.except_osv("Error !", "Don't take the vlan 1 for tunnels on %s/%s!" % (iface.name,self.unit.name))
               
        self.properties["vtun.enabled"]=False  
        #       
        vtun_initf =  open(os.path.join(init_dir,"vtun"),"w")        
        vtun_initf.write("""#!/bin/sh /etc/rc.common
# Copyright (C) 2006 OpenWrt.org

START=41
STOP=89

start() {
        mkdir -p /var/lock/vtund
        %s
}

stop() {
        killall vtund
}""" % ("\n        ".join(vtun_start),) )
        vtun_initf.close() 
        #                
        if vtunf:
            self.properties["vtun.enabled"]=True            
            vtunf.close()
            
        
        #############################################################
        # write interface configuration
        #############################################################
        
        ifacef = open(os.path.join(cfg_dir,"network"),"w")
        ifacef.write(self.switch_header_get())
        ifacef.write("""config interface 'loopback'
    option ifname 'lo'
    option proto 'static'
    option ipaddr '127.0.0.1'
    option netmask '255.0.0.0'
    
""")
        for iface in self.unit.iface_ids:                   
            ifacef.write("config interface '%s'\n" %(iface.name,))
            ifacef.write("    option ifname '%s'\n" % (iface.code,))
            if len(iface.port_ids) > 1 or iface.id in bridged_iface_ids:
                ifacef.write("    option type 'bridge'\n")
            
            iface_net = iface_ipv4_get(iface)
            if iface_net:                
                ifacef.write("    option proto 'static'\n")
                ifacef.write("    option ipaddr '%s'\n" % (iface_net,))
                ifacef.write("    option netmask '%s'\n" % (iface_net.netmask(),))
                
                for gw_iface in iface.gw_iface_ids:
                    gw_ip = iface_ipv4_get(gw_iface)
                    if gw_ip:
                        ifacef.write("    option gateway '%s'\n" % (gw_ip,))                        
                        break
                
                for dns_iface in iface.dns_iface_ids:
                    dns_net = iface_ipv4_get(dns_iface)
                    if dns_net:
                        ifacef.write("    list dns '%s'\n" % (dns_net,))
                        if not iface.private and iface.type=="gw":               
                            olsr_dns_ip4.append(dns_net)
                        
            elif iface.dhcp:
                ifacef.write("    option proto 'dhcp'\n")
            else:
                ifacef.write("    option proto 'none'\n")
            ifacef.write("\n")
            
        ifacef.close()

        #############################################################
        # write firewall configuration
        #############################################################
        
        firewallf = open(os.path.join(cfg_dir,"firewall"),"w")
        firewallf.write(self.firewall_header_get())
        firewallf.write("\n")
                
        #check interfaces
        forwards = []        
        private_ipv4_nets = []
        private_ifaces = []
        protected_ifaces = []
        for iface in self.unit.iface_ids:            
            parent = iface.parent_id
            #if not parent:
            #    raise osv.except_osv("Error !", "No Network for interface %s of unit %s defined!" % (iface.name, self.unit.name))
            if parent:
                net_ip = net_ipv4_get(parent)
                if net_ip:
                    if parent.private:
                        private_ifaces.append(iface)
                        private_ipv4_nets.append(net_ip)                
                    if parent.protected:
                        protected_ifaces.append(iface)
        
        for iface in self.unit.iface_ids:
            parent = iface.parent_id            
            firewallf.write("config zone\n")
            firewallf.write("    option name %s\n" % (iface.name,)) 
            firewallf.write("    option network '%s'\n" % (iface.name,))
            
            if parent.private:
                firewallf.write("    option input    ACCEPT\n")
                firewallf.write("    option output   ACCEPT\n")
                firewallf.write("    option forward  REJECT\n")                
                                
            elif parent.protected:
                firewallf.write("    option input    ACCEPT\n")
                firewallf.write("    option output   ACCEPT\n")
                firewallf.write("    option forward  ACCEPT\n")
                if private_ipv4_nets:
                    firewallf.write("    option masq     1\n")
                    masq_src = []                    
                    for private_net in private_ipv4_nets:
                        masq_src.append("%s/%s" % (private_net,private_net.mask))                        
                    firewallf.write("    option masq_src '%s'\n" % (" ".join(masq_src),))
                    #add forwards from private interfaces
                    for private_iface in private_ifaces:
                        forwards.append((private_iface,iface))
                             
            elif parent.public:
                if iface.type=="link":
                    firewallf.write("    option input    REJECT\n")
                    firewallf.write("    option output   ACCEPT\n")
                    firewallf.write("    option forward  ACCEPT\n")                    
                elif iface.type=="gw":
                    firewallf.write("    option input    REJECT\n")
                    firewallf.write("    option output   ACCEPT\n")
                    firewallf.write("    option forward  REJECT\n")
                    firewallf.write("    option masq     1\n")
                    firewallf.write("    option mtu_fix  1\n")                    
                    #add forward from private interfaces 
                    for private_iface in private_ifaces:
                        forwards.append((private_iface,iface))
                    #add forward from protected interfaces           
                    for protected_iface in protected_ifaces:
                        forwards.append((protected_iface,iface))                    
                elif iface.tpye=="site":
                    firewallf.write("    option input    ACCEPT\n")
                    firewallf.write("    option output   ACCEPT\n")
                    firewallf.write("    option forward  REJECT\n")
            
            firewallf.write("\n")
        
        #write forwards
        for src_iface,dest_iface in forwards:            
            firewallf.write("config forwarding\n")
            firewallf.write("    option src %s\n" % (src_iface.name,))
            firewallf.write("    option dest %s\n" % (dest_iface.name,))
            firewallf.write("\n")
                    
        firewallf.close()
        
    
        #############################################################
        # write wlan configuration
        #############################################################
    
        wlanf = open(os.path.join(cfg_dir,"wireless"),"w")
        wlanf.write(self.wlan_header_get())
        
        wlan_port_cfg = False        
        for port in self.unit.port_ids:
            if port.wlan_available and port.enabled:
                port_iface = port.iface_id
                if not port_iface:
                    raise osv.except_osv(_("Error !"), _("No interface for port %s on unit %s defined") % (port.name,self.unit.name))
                    
                if not wlan_port_cfg:
                    wlan_port_cfg = True
                    if self.wlan_port.wlan_txpower:
                        wlanf.write("    option txpower    %s\n" % (self.wlan_port.wlan_txpower,))
                    wlanf.write("    option disabled    0\n")
                                    
                wlanf.write("\n")
                wlanf.write("config wifi-iface\n")
                wlanf.write("    option device     %s\n" % (self.wlan_device_get(),))
                wlanf.write("    option network    %s\n" % (port_iface.name,))            
                wlanf.write("    option mode       %s\n" % (port.mode_type=="client" and "sta" or "ap",))
                wlanf.write("    option ssid       '%s'\n" % (port.wlan_ssid,))
                if port.wlan_ssid_hidden:
                    wlanf.write("    option hidden     1\n")            
                if port.wlan_wds:
                    wlanf.write("    option wds        1\n")
                if port.wlan_auth_mode == "psk":
                    wlanf.write("    option encryption psk+tkip+ccmp\n")
                    wlanf.write("    option key        '%s'\n" % (port.wlan_psk,))
                else:
                    raise osv.except_osv(_("Error !"), _("Only Preshared Key supported now for unit %s") % (self.unit.name,))
                
        if not wlan_port_cfg:
            wlanf.write("    option disabled    1\n")
        
        wlanf.write("\n")        
        wlanf.close()
        
        
        #############################################################
        # write DNS configuration
        #############################################################
        
        dhcpf = open(os.path.join(cfg_dir,"dhcp"),"w")
        dhcpf.write("""config dnsmasq
    option domainneeded      1
    option boguspriv         1
    option filterwin2k       0  # enable for dial on demand
    option localise_queries  1
    option rebind_protection 0  # disable if upstream must serve RFC1918 addresses
    option rebind_localhost  1  # enable for RBL checking and similar services        
    option local    '/lan/'
    option domain   'lan'
    option expandhosts      1
    option nonegcache       0
    option authoritative    1
    option readethers       1
    option leasefile    '/tmp/dhcp.leases'                
""")
        if has_olsr and not self.gateway_iface:
            dhcpf.write("    option resolvfile    '/var/run/resolvconf_olsr'\n")
        else:
            dhcpf.write("    option resolvfile    '/tmp/resolv.conf.auto'\n")
            
        if has_olsr:
            dhcpf.write("    list addnhosts    '/var/run/hosts_olsr'\n")
        
        dhcpf.write("\n")
        dhcp_iface_ids = []
        if self.dns_service:
            dhcp_iface_ids = [i.id for i in self.dns_service.iface_ids]
            
        for iface in self.unit.iface_ids:
            dhcpf.write("config dhcp %s\n" % (iface.name,))
            dhcpf.write("    option interface %s\n" % (iface.name,))
            if iface.id in dhcp_iface_ids and iface.ipv4_ip and iface.ipv4_mask:
                dhcp_net = ipcalc.Network(iface.ipv4_ip,iface.ipv4_mask,version=4)
                dhcp_space = (dhcp_net.size()-2) / 3.0
                if dhcp_space >= 4:
                    dhcp_bits = util.bits(dhcp_space)
                    dhcp_net = ipcalc.Network(long(dhcp_net.host_first())+(2**dhcp_bits),32-dhcp_bits)
                    dhcpf.write("    option start      %s\n" % (str(dhcp_net).split(".")[3],)) 
                    dhcpf.write("    option limit      %s\n" % (dhcp_net.size()-2,))
                    dhcpf.write("    option leasetime  48h\n")
                    dhcpf.write("    option ignore     0\n")                    
                else:
                    dhcpf.write("    option ignore    1\n") 
            else:
                dhcpf.write("    option ignore    1\n")
            dhcpf.write("\n")
            
        dhcpf.close()
          
        #############################################################
        # write OLSR configuration
        #############################################################
          
        olsr_basicf=open(os.path.join(cfg_dir,"olsrd"),"w")
        olsr_basicf.write("""config olsrd
    option config_file '/etc/olsrd.conf'
        """)
        olsr_basicf.close()
        
        olsrf=open(os.path.join(etc_dir,"olsrd.conf"),"w")        
        olsrf.write(self.olsr_config_txt())
        olsrf.write("\n\n")                                                                                                                   
        olsrf.write(self.olsr_config_txt("olsrd_arprefresh.so.0.1"))                                                                                                                                           
        olsrf.write("\n\n")      
        olsrf.write(self.olsr_config_txt("olsrd_txtinfo.so.0.1"))
        olsrf.write("\n\n")
        olsrf.write('LoadPlugin "olsrd_nameservice.so.0.3"\n')
        olsrf.write('{\n')
        olsrf.write('    PlParam "name" "%s"\n' % (self.hostname,))
        olsrf.write('    PlParam "sighup-pid-file" "/var/run/dnsmasq.pid"\n')
        address = self.unit.address_id
        if address and address.lon and address.lat:
            olsrf.write('    PlParam "lat" "%s"\n' % (address.lon,))
            olsrf.write('    PlParam "lon" "%s"\n' % (address.lat,))
        
        if has_olsr and olsr_dns_ip4:            
            for ipv4 in olsr_dns_ip4:                
                olsrf.write('    PlParam "dns-server" "%s"\n' % (ipv4,))                
        olsrf.write("}\n\n")
   
        if self.gateway_iface:
            gw_net = self.gateway_iface.network_id
            if gw_net and gw_net.published:
                olsrf.write(self.olsr_config_txt("olsrd_dyn_gw.so.0.5"))
                olsrf.write("\n")
                
        olsrf.write('Hna4\n{\n')
        for iface in self.unit.iface_ids:
            hna_net = iface.network_id and iface.network_id.parent_id or None
            if hna_net and hna_net.published and iface.type!="gw" and not hna_net.private:
                hna_ip = net_ipv4_get(hna_net)                
                if hna_ip:
                    olsrf.write('    %s %s\n' % (hna_ip,hna_ip.netmask()))
        olsrf.write('}\n\n')
        olsrf.write(self.olsr_config_txt("InterfaceDefaults"))
        olsrf.write("\n\n")
        if has_olsr:
            for iface in self.olsr_service.iface_ids:
                if iface.code:
                    iface_mode="ether"
                    iface_name = iface.code
                    ports = iface.port_ids
                    if len(ports) > 1:
                        iface_name = "br-%s" % (iface.name,)
                    
                    for port in ports:
                        if port.wlan_available:                
                            iface_mode="mesh"
                            break                        
                    olsrf.write('''Interface "%s" {
    Mode "%s"
}                
''' % (iface_name,iface_mode))
                    olsrf.write("\n")
        #
        #        
        olsrf.close()
        
        
        #############################################################
        # write QOS config
        #############################################################
        
        qosf = open(os.path.join(cfg_dir,"qos"),"w")
        qosf.write(
'''
# QoS configuration for OpenWrt

# INTERFACES:
''')
        
        
        for iface in self.unit.iface_ids:
            qos_profile = iface.qos_profile_id   
            if qos_profile:
                self.properties["qos.enabled"]=True        
                qosf.write('''
config interface %s
    option classgroup "Default"
    option enabled     1
    option upload      %s
    option download    %s
''' % (iface.name, int(qos_profile.upload), int(qos_profile.download) ) )
            
        
        
        qosf.write(
'''

# QOS RULES:
config classify
    option target       "Priority"
    option ports        "22,53"
config classify
    option target       "Normal"
    option proto        "tcp"
    option ports        "20,21,25,80,110,443,993,995"
config classify
    option target       "Express"
    option ports        "5190"
config default
    option target       "Express"
    option proto        "udp"
    option pktsize      "-500"
config reclassify
    option target       "Priority"
    option proto        "icmp"
config default
    option target       "Bulk"
    option portrange    "1024-65535"
config reclassify
    option target       "Priority"
    option proto        "tcp"
    option pktsize      "-128"
    option mark         "!Bulk"
    option tcpflags     "SYN"
config reclassify
    option target       "Priority"
    option proto        "tcp"
    option pktsize      "-128"
    option mark            "!Bulk"
    option tcpflags     "ACK"


# Don't change the stuff below unless you
# really know what it means :)

config classgroup "Default"
    option classes      "Priority Express Normal Bulk"
    option default      "Normal"


config class "Priority"
    option packetsize  400
    option maxsize     400
    option avgrate     10
    option priority    20
config class "Priority_down"
    option packetsize  1000
    option avgrate     10


config class "Express"
    option packetsize  1000
    option maxsize     800
    option avgrate     50
    option priority    10

config class "Normal"
    option packetsize  1500
    option packetdelay 100
    option avgrate     10
    option priority    5
config class "Normal_down"
    option avgrate     20

config class "Bulk"
    option avgrate     1
    option packetdelay 200
''')
        qosf.close()