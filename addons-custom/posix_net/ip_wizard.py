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

from openerp.osv import fields, osv


class posix_net_ip_wizard(osv.osv_memory):

    def _max_bits_get(self):
        return 0   
    
    def _ip_version_get(self):
        return ""
    
    def _ip_object_get(self, cr, uid, ids, context=None):
        return None
        
    def on_change_auto_config(self, cr, uid, ids, select, ip_pool_id, context=None):
        network_obj=self.pool.get("posix_net.network")    
        res_value = {
            "network_ids" : None
        }    
        res = {
            "value" : res_value
        }                
        ip_boolean = self._ip_version_get()
        ip_address_id = ip_boolean + "_address_id"
        parent_ip_address_id = "parent_id."+ip_address_id

        if select:
            network_set = set()     
            for oid in network_obj.search(cr, uid, [(ip_boolean,"=",True), (ip_address_id,"=",None), ("parent_id", "=", None)]):
                network_set.add(oid)
            for oid in network_obj.search(cr, uid, [(ip_boolean,"=",True), (ip_address_id,"=",None), (parent_ip_address_id, "!=", None)]):
                network_set.add(oid)                
            if network_set:
                res_value["network_ids"]=list(network_set)                        
        return res
         
    def on_change_datas(self, cr, uid, ids, has_subnet, has_mask, has_hosts, subnet, networkmask, hosts, ip_pool_id, context=None):
        res = {
                "value" : {}
            }

        ip_address_obj = self._ip_object_get(cr, uid, ids, context)
        ip_pool = ip_pool_id and ip_address_obj.browse(cr,uid,ip_pool_id,context) or None
        if ip_pool:
            real_netmask=ip_pool.mask
            max_bits_ip = int(self._max_bits_get())
            ### Calculator ###
            maxbits = 2**((max_bits_ip-2)-(real_netmask-1))
            
            ## If networkmask is set ##
            has_networkmask_potency = max_bits_ip-networkmask
            has_networkmask_host = (2**has_networkmask_potency)-2
            has_networkmask_subnet = 2**(networkmask%8)
            
            ## If subnet is set ##
            bits_subnet=0
            if has_subnet:
                subnet-=1
            while(subnet >= (1<<bits_subnet)):
                bits_subnet+=1
    
            has_subnet_networkmask = bits_subnet+(real_netmask-1)
            has_subnet_potency = max_bits_ip-has_subnet_networkmask
            has_subnet_host = (2**has_subnet_potency) -2
            
            ## If host is set ##
            bits_host = 0
            while (hosts >= (1 << bits_host)):
                bits_host+=1
            has_host_networkmask = max_bits_ip-bits_host
            has_host_subnet = 2**(has_host_networkmask%8)
            
            ## Calculates with the minimum networkmask, so there is no wrong outcome / Example: Mask = 24, Real Mask = 25 ##
            real_potency = max_bits_ip-real_netmask #     7
            real_host= (2**real_potency)-2 #     126
            real_subnet = 2**((real_netmask)%8)# 2
            
            ### If the conditions apply ###
            ## If input is wrong ##      
            # If the input does not fit with the minimum networkmask, depends on the networkpool's mask #         
            if hosts > real_host:
                res["value"]["networkmask"] = real_netmask
                res["value"]["number_of_hosts"] =  real_host
                res["value"]["subnet"] = real_subnet
                
            elif networkmask < real_netmask:
                res["value"]["networkmask"] = real_netmask
                res["value"]["number_of_hosts"] =  real_host
                res["value"]["subnet"] = real_subnet
                
            elif subnet < real_subnet:
                res["value"]["networkmask"] = real_netmask
                res["value"]["number_of_hosts"] =  real_host
                res["value"]["subnet"] = real_subnet  
            # If the input is smaller or bigger than the minimum value it can be
            elif hosts <= 1:
                res["value"]["number_of_hosts"] = 2
                res["value"]["networkmask"] = max_bits_ip-2
                res["value"]["subnet"] = 64
                
            elif networkmask > (max_bits_ip-2):
                res["value"]["networkmask"] = max_bits_ip-2
                res["value"]["number_of_hosts"] = 2
                res["value"]["subnet"] = 64               
                
            elif (subnet+1) > maxbits and has_subnet:
                res["value"]["subnet"] = maxbits
    
            ## If input is right ##
            elif not has_hosts and not has_subnet:
                res["value"]["number_of_hosts"] =  has_networkmask_host
                res["value"]["subnet"] = has_networkmask_subnet
                
            elif not has_mask and not has_hosts:
                res["value"]["number_of_hosts"] = has_subnet_host
                res["value"]["networkmask"] = has_subnet_networkmask
            
            elif not has_mask and not has_subnet:
                res["value"]["networkmask"] = has_host_networkmask
                res["value"]["subnet"] = has_host_subnet
                
        return res
    
    def do_next(self, cr, uid, ids, context=None):
        ip_address_key = self._ip_version_get() + "_address_id"
        network_obj=self.pool.get("posix_net.network")    
        ip_obj = self._ip_object_get(cr, uid, ids, context)
        for obj in self.browse(cr, uid, ids, context):
            ip_address = obj.network_pool
            ip_mask = obj.networkmask
            hosts = obj.number_of_hosts
            ip_version = self._ip_version_get()
            ip_bits = self._max_bits_get()
            
            for network in obj.network_ids:
                ip_id = None
                if network.endpoint:
                    ip_id = ip_obj.address_aquire(cr, uid, ip_address.id, network.name, ip_bits, 1, context)
                else:
                    ip_id = ip_obj.address_aquire(cr, uid, ip_address.id, network.name, ip_mask, hosts, context)
                values = {
                  ip_address_key : ip_id,
                  ip_version : True 
                }                                
                network_obj.write(cr, uid, network.id, values, context)
        return { "type" : "ir.actions.act_window_close" }
    
    _name = "posix_net.ip_wizard"
    _description = "IP Wizard"

    _columns = {                
        "number_of_hosts" : fields.integer("Hosts", required=True,
                                                help="The number of hosts. You can only enter a specific value, depends on the IP Pool's networkmask."),        
        "networkmask" : fields.integer("Bits", required=True,
                                            help="The networkmask. You can only enter a specific value, depends on the IP Pool's networkmask."),
        "subnet" : fields.integer("Subnets", required=True,
                                  help="The subnets. You can only enter a specific value, depends on the IP Pool's networkmask"),
                
        "auto_config" : fields.boolean("Auto Configuration",help="This checkbox does an auto selection of networks and interfaces to configure"),
    }

       

class posix_net_ipv4_wizard(osv.osv_memory):
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(posix_net_ip_wizard,self).default_get(cr,uid,fields_list,context)
        active_ids = context.get("active_ids")        
        if active_ids and len(active_ids)==1:
            res["network_pool"]=active_ids[0]
        return res
    
    def _max_bits_get(self):
        return 32    
    
    def _ip_version_get(self):
        return "ipv4"
    
    def _ip_object_get(self, cr, uid, ids, context=None):
        ipv4_obj = self.pool.get("posix_net.net_ipv4_address")
        return ipv4_obj

    _inherit="posix_net.ip_wizard"
    _name = "posix_net.ipv4_wizard"
    _description = "IPv4 Wizard"
    _columns = {
        "network_pool" : fields.many2one("posix_net.net_ipv4_address", "IP Pool", required=True,
                                        help="This IP Address is the parent of the entered networks. The IP Addresses, which will be assigned, depend on the number of hosts"),        
        "network_ids" : fields.many2many("posix_net.network", "ipv4_wizard_rel", "wizard_id", "network_id", "Network")
    }
    _defaults={
        "number_of_hosts" : 2,    
        "networkmask" : 30,
        "subnet" : 64
    }   
       

class posix_net_ipv6_wizard(osv.osv_memory):
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(posix_net_ip_wizard,self).default_get(cr,uid,fields_list,context)
        active_ids = context.get("active_ids")        
        if active_ids and len(active_ids)==1:
            res["network_pool"]=active_ids[0]
        return res
    
    def _max_bits_get(self):
        return 128
    
    def _ip_version_get(self):
        return "ipv6"
    
    def _ip_object_get(self, cr, uid, ids, context=None):
        ipv6_obj = self.pool.get("posix_net.net_ipv6_address")
        return ipv6_obj
        
    _inherit="posix_net.ip_wizard"       
    _name = "posix_net.ipv6_wizard"
    _description = "IPv6 Wizard"
    _defaults = {
        "number_of_hosts" : 2,
        "networkmask" : 126,
        "subnet" : 64
    }
    _columns = {
        "network_pool" : fields.many2one("posix_net.net_ipv6_address", "IP Pool", required=True,
                                        help="This IP Address is the parent of the entered networks. The IP Addresses, which will be assigned, depend on the number of hosts"),   
        "network_ids" : fields.many2many("posix_net.network", "ipv6_wizard_rel", "wizard_id", "network_id", "Network")
        
    }
    
