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
import ipcalc
from openerp.tools.translate import _
from openerp.addons.at_base import util

class posix_net_net_address(osv.AbstractModel):
   
    def _ip_version(self):
        return 0
    
    def _max_bits_get(self):
        return 0   
             
    def _is_subnet(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids,False)
        for obj in self.browse(cr, uid, ids, context):
            if obj.mask == self._max_bits_get() or obj.mask == 0:
                res[obj.id]=False
            else:               
                res[obj.id]=True
        return res
                
    def _ip_hex(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = ipcalc.Network(obj.ip).hex()
        return res
        
    def _childs_reverse_get(self, cr, uid, oid, context):
        return None
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ["name","ip", "mask"], context=context)
        res = []
        unit_view = context.get("unit_view")           
        for record in reads:            
            if unit_view:
                net_str = record["ip"]
            else:
                net_str = "%s/%s | %s" % (record["ip"],record["mask"],record["name"])                        
            res.append((record["id"], net_str))
        return res
        
    def address_aquire(self, cr, uid, oid, ip_name, ip_mask, hosts, context=None):
        ip_found_calc = None
        ip_pool = self.browse(cr,uid,oid,context)            
        ip_childs = self._childs_reverse_get(cr, uid, oid, context) 
        ip_version = self._ip_version()   
        ip_max_bits = self._max_bits_get()                
        
        ip_pool_calc = ipcalc.Network(ip_pool.ip,ip_pool.mask,ip_version)
        if ip_childs:                                                
            ip_last_calc = None 
            for ip in ip_childs:               
                ip_calc = ipcalc.Network(ip.ip,ip.mask,version=ip_version)
                ip_next_calc = ipcalc.Network(long(ip_calc.broadcast())+1,ip_mask,version=ip_version)
                if ip_mask < ip_max_bits:           
                    #check for different network sizes / masks     
                    ip_next_net_calc = ipcalc.Network(long(ip_next_calc.network()),ip_mask,version=ip_version)
                    while long(ip_next_net_calc.host_first()) < long(ip_next_calc):
                        ip_next_net_calc=ipcalc.Network(long(ip_next_net_calc.broadcast())+1,ip_mask,version=ip_version)#
                    ip_next_calc=ip_next_net_calc
                    

                if not ip_last_calc:
                    if ( long(ip_next_calc.broadcast()) <= long(ip_pool_calc.broadcast()) ):
                        ip_found_calc = ip_next_calc
                        break
                else:
                    next_ip = ipcalc.Network(long(ip_next_calc) + hosts, version=ip_version)
                    if ( next_ip < ip_last_calc ):                        
                        ip_found_calc = ip_next_calc
                        break
                ip_last_calc = ip_calc          
            if not ip_found_calc and long(ip_last_calc) != long(ip_pool_calc):
                ip_next_calc = ipcalc.Network(long(ip_calc.broadcast()),ip_mask,version=ip_version)
                if ip_next_calc.broadcast() < ip_last_calc:
                    ip_found_calc = ip_pool_calc
                
              
        else:
            if ip_mask > ip_pool.mask:                
                ip_found_calc = ip_pool_calc  
                
        if not ip_pool_calc:
            raise osv.except_osv(_('Error!'),_('You have reached the maximum of the available IP Addresses! Please make a new IP Pool.'))
      
        ip_found = str(ip_found_calc)
        if ip_max_bits == ip_mask:
            ip_found = str(ip_found_calc.host_first())
            
        return self.create(cr, uid, { "parent_id" : oid, 
                                "name" : ip_name,
                               "ip" : ip_found,
                               "mask" : ip_mask }, context)
    
    def address_aquire_next(self,cr,uid,oid,ip_name,hosts=1,endpoint=True,context=None):
        if endpoint:
            return self.address_aquire(cr, uid, oid, ip_name, self._max_bits_get(), 1, context)
        else:             
            ip_max_bits = self._max_bits_get()
            ip_bits_needed = util.bits(hosts)
            ip_mask = ip_max_bits-ip_bits_needed
            pool = self.browse(cr, uid, oid, context)
            if ip_mask < pool.mask:
                raise osv.except_osv(_("Error !"), _("Required subnet is creater then the parent network"))
            return self.address_aquire(cr, uid, oid, ip_name, ip_mask, hosts, context)
             
    _name="posix_net.net_address"
    _description="IP Pool"
    
    _columns = {
        "name" : fields.char("Name", size=128),
        "ip" : fields.char("IP", size=128),
        "ip_hex" : fields.function(_ip_hex, type="char", size=32, store=True, string="IP Number in Hex"),
        "mask" : fields.integer("Network Mask"),       
        "subnet" : fields.function(_is_subnet, type="boolean", method=True, store=True, string="Is Subnet",select=True)
    }
    _order = "ip_hex ASC"


class posix_net_net_ipv4_address(osv.Model):
    
    def _childs_reverse_get(self, cr, uid, oid, context):
        return self.browse(cr, uid,self.search(cr, uid, [("parent_id","=",oid)], order="ip desc", context=context),context)
         
    def _max_bits_get(self):
        return 32
    
    def _ip_version(self):
        return 4
    
    _name="posix_net.net_ipv4_address"
    _inherit="posix_net.net_address"
    _description="IPv4 Address"
    _columns = {
        "parent_id" : fields.many2one("posix_net.net_ipv4_address", "Parent"),
        "child_ids" : fields.one2many("posix_net.net_ipv4_address", "parent_id", "Childs")
    }   


class posix_net_net_ipv6_address(osv.Model):


    def _childs_reverse_get(self, cr, uid, oid, context):
        return self.browse(cr, uid,self.search(cr, uid, [("parent_id","=",oid)], order="ip desc", context=context),context)        
         
    def _max_bits_get(self):
        return 128  
    
    def _ip_version(self):
        return 6
    
    _name="posix_net.net_ipv6_address"
    _inherit="posix_net.net_address"   
    _description="IPv6 Address"
    _columns = {
        "parent_id" : fields.many2one("posix_net.net_ipv6_address", "Parent"),
        "child_ids" : fields.one2many("posix_net.net_ipv6_address", "parent_id", "Childs")
    }   
