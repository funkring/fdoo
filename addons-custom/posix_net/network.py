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
from openerp.tools.translate import _
from openerp.addons.at_base import util
from openerp.addons.at_base import extfields
import openerp.addons.decimal_precision as dp
#from openerp.addons.at_pos.escpos import Escpos

class posix_net_network(osv.Model):
     
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ["name", "parent_id"], context=context)
        res = []
        for record in reads:
            name = record["name"]
            if record["parent_id"]:
                name = record["parent_id"][1] + " / " + name
            res.append((record["id"], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)
   
    def on_change_visibility(self, cr, uid, ids, public, private, context=None):
        res = {
            "value" : {}
        }
        if public:
            res["value"]["private"]=False
        if private:
            res["value"]["public"]=False
        return res
    
    def do_validate(self,cr,uid,ids,context=None):
        ipv4_pool_obj=self.pool.get("posix_net.net_ipv4_address")
        ipv6_pool_obj=self.pool.get("posix_net.net_ipv6_address")
        
        for network in self.browse(cr,uid,ids,context):
            parent = network.parent_id            
            if parent:
                self.do_validate(cr,uid,[parent.id],context)            
                parent = self.browse(cr,uid,parent.id,context)
                                                            
            if network.hosts or network.endpoint:
                if parent and network.endpoint and not parent.leaf:
                    raise osv.except_osv(_("Error !"), _("Cannot aquire IP address for an endpoint on network which support no leaf types"))
            
                if network.ipv4 and not network.ipv4_address_id:
                    ip_pool = parent and parent.ipv4_address_id or None
                    if not ip_pool:
                        raise osv.except_osv(_("Error !"), _("There is no parent with valid IPv4 address pool defined for network %s") % (network.name, ))                
                    new_address_id = ipv4_pool_obj.address_aquire_next(cr,uid,ip_pool.id,network.name,
                                                                       hosts=network.hosts,endpoint=network.endpoint)
                    self.write(cr,uid,network.id,{"ipv4_address_id" : new_address_id })
                if network.ipv6 and not network.ipv6_address_id:
                    ip_pool = parent and parent.ipv6_address_id or None
                    if not ip_pool:
                        raise osv.except_osv(_("Error !"), _("There is no parent with valid IPv6 address pool defined for network %s") % (network.name, ))

                    new_address_id = ipv6_pool_obj.address_aquire_next(cr,uid,ip_pool.id,network.name,
                                                                       hosts=network.hosts,endpoint=network.endpoint)
                    self.write(cr,uid,network.id,{"ipv6_address_id" : new_address_id })
                
                
    def _is_leave(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids):
            if obj.child_ids:
                for child in obj.child_ids:
                    if child.endpoint:
                        res[obj.id]=True
                    else:
                        res[obj.id]=False
                        break
        return res
    
    
    def _relids_network_parent(self, cr, uid, ids, context=None):
        res = list(ids)
        res.extend(self.search(cr, uid, [("parent_id", "child_of", ids)]))
        return res
    
    _name = "posix_net.network"
    _description = "Network"
    _order = "complete_name"
    _columns = {
        "name" : fields.char("Name", size=128, select=True, required=True),
        "complete_name": fields.function(_name_get_fnc, method=True, type="char", size=256, string="Name", select=True, store = {
                                                "posix_net.network" : (_relids_network_parent, ["parent_id", "name"],10)
                                            }),
        "parent_id" : fields.many2one("posix_net.network", "Parent", select=True,
                                      help="The current network is part of the parent network"),
        "child_ids" : fields.one2many("posix_net.network","parent_id", "Childs"),     
        "ipv4" : fields.boolean("IPv4"),
        "ipv6" : fields.boolean("IPv6"),
        "ipv4_address_id" : fields.many2one("posix_net.net_ipv4_address", "IPv4 Address"),
        "ipv6_address_id" : fields.many2one("posix_net.net_ipv6_address", "IPv6 Address"),
        "hosts" : fields.integer("Hosts"),
        "endpoint" : fields.boolean("Endpoint",select=True),
        "private" : fields.boolean("Private",help="Private Network, not reachable from outsite, secured with NAT"),
        "public" : fields.boolean("Public",help="Public Network (with public IPs) fully reachable from outsite"),
        "protected" : fields.boolean("Protected",help="Protected Network only reachable from internal links"),
        "published" : fields.boolean("Published",help="A network which should be announced"),
        "leaf" : fields.function(_is_leave, type="boolean", method=True,string="Leaf"),
        "is_template": fields.boolean("Template",help="Network Leaf node could be assigned more than once")
          
    } 
 

class posix_net_unit(osv.Model):
       
    #def _get_unit(self, cr, uid, ids, context=None):
    #    return None
    
    def _print_label(self,cr,uid,oid,printer_id,context):
        unit = self.browse(cr,uid,oid,context)
        #pos_printer = self.pool.get("at_pos.pos_printer")._get_printer(cr,uid,printer_id,context)

        printer = None #Escpos(pos_printer.name)                        
        try:
            printer.hw("INIT")                
            
            #print header
            printer.set(align="left",height=2,width=2)            
            printer.text(unit.name)
            printer.text("\n")
            
            #configure default font
            printer.set(align="left",height=1,width=1)
            printer.set(align="left",height=1,width=1)
            
            #print address
            address = unit.address_id
            partner = address and address.partner_id or None
            if partner:
                #print name
                address_name = address.name or partner.name or ""                 
                printer.ltext(address_name,0.5)

                #print phone
                phone = address.mobile or address.phone or ""
                if phone:
                    printer.rtext(phone,0.5,overflow="\n")
                    
                printer.text("\n")
                
                #print address
                if address.street:
                    printer.text(address.street+"\n")
                if address.zip:
                    printer.text(address.zip + " ")
                if address.city:
                    printer.text(address.city + "\n")
                                    
            for port in unit.port_ids:
                if port.wlan_ssid and not port.wlan_ssid_hidden:
                    printer.text("\n") 
                    printer.text("WLAN SSID: %s\n" % (port.wlan_ssid,))
                    printer.text("WLAN PSK:  %s\n" % (port.wlan_psk,))
                                        
            printer.cut()
        finally:
            printer.close()            
        return True        
   
    def do_label_print(self, cr, uid, ids, context=None):
        for oid in ids:
            self._print_label(cr, uid, oid, None, context)
        return True
    
    def copy(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}
        if not default.has_key("login"):
            default["login"]="franzi"
        if not default.has_key("password"):
            default["password"]=util.password()
        if not default.has_key("service_ids"):
            default["service_ids"]=None
        if not default.has_key("port_ids"):
            default["port_ids"]=None
        if not default.has_key("iface_ids"):
            default["iface_ids"] = None
        if not default.has_key("vlan_ids"):
            default["vlan_ids"]=None
        if not default.has_key("vlan_port_ids"):
            default["vlan_port_ids"]=None
                  
        copy_id =  super(posix_net_unit,self).copy(cr,uid,oid,default,context)
        return copy_id
    
    def do_init(self, cr, uid, ids, context=None):
        port_obj = self.pool.get("posix_net.port")
        iface_obj = self.pool.get("posix_net.iface")
        service_obj = self.pool.get("posix_net.service")
        vlan_obj = self.pool.get("posix_net.vlan")
        vlan_port_obj = self.pool.get("posix_net.vlan_port")
        for unit in self.browse(cr,uid,ids,context):
            unit_type = unit.type_id            
            ports = unit.port_ids
            services = unit.service_ids
            ifaces = unit.iface_ids                  
            vlan = unit.vlan_ids  
            vlan_ports = unit.vlan_port_ids        
            if unit_type and unit_type.template_unit_id:
                if not ifaces:
                    for iface_def in unit_type.template_unit_id.iface_ids:
                        default = {}
                        default["unit_id"] = unit.id
                        default["name"] = iface_def.name
                        if iface_def.parent_id.is_template:
                            default["network_id"] = iface_def.network_id.id
                        iface_obj.copy(cr, uid, iface_def.id, default, context=context)
                        
                if not services:                    
                    for service_def in unit_type.template_unit_id.service_ids:
                        default = {}
                        default["unit_id"] = unit.id
                        default["iface_ids"] = [(6, 0, iface_obj.search(cr, uid, [("unit_id", "=", unit.id)]))]
                        service_obj.copy(cr, uid, service_def.id, default, context=context)
                                         
                if not ports:             
                    for port_def in unit_type.template_unit_id.port_ids:
                        default = {}
                        default["sequence"] = port_def.sequence
                        default["unit_id"] = unit.id
                        default["wlan_ssid"] = None
                        if port_def.iface_id:
                            iface_ids = iface_obj.search(cr,uid,[("unit_id","=",unit.id),("name","=",port_def.iface_id.name)])
                            default["iface_id"]=iface_ids and iface_ids[0] or None
                    
                        port_obj.copy(cr, uid, port_def.id, default, context=context)
                if not vlan:
                    for vlan in unit_type.template_unit_id.vlan_ids:
                        default = {}
                        default["unit_id"] = unit.id
                        vlan_obj.copy(cr, uid, vlan.id, default, context=context)
                if not vlan_ports:
                    for vlan_port in unit_type.template_unit_id.vlan_port_ids:
                        default = {}
                        default["unit_id"] = unit.id
                        if vlan_port.vlan_id:
                            vlan_ids = vlan_obj.search(cr, uid, [("unit_id", "=", unit.id), ("vlan", "=", vlan_port.vlan_id.vlan), ("device", "=", vlan_port.vlan_id.device)])
                            default["vlan_id"] = vlan_ids and vlan_ids[0] or None
                        if vlan_port.port_id:
                            vlan_port_ids = port_obj.search(cr, uid, [("unit_id", "=", unit.id), ("sequence", "=", vlan_port.port_id.sequence)])
                            default["port_id"] = vlan_port_ids and vlan_port_ids[0] or None
                        vlan_port_obj.copy(cr, uid, vlan_port.id, default, context=context)
                self.write(cr, uid, unit.id, {"state" : "init"}, context)
            else:
                raise osv.except_osv(_("Error !"), _("Either there is no unit type for unit %s set or the unit type does not have a unit template!") % (unit.name,))
        
        #ensure endpoint is true
        iface_obj.write(cr,uid,iface_obj.search(cr,uid,[("unit_id","in",ids)]),{"endpoint" : True} )
        return True
              
    def do_validate(self,cr,uid,ids,context=None):
        port_obj = self.pool.get("posix_net.port")
        iface_obj = self.pool.get("posix_net.iface")
                
        #ensure endpoint is true
        iface_ids = iface_obj.search(cr,uid,[("unit_id","in",ids)])    
        iface_obj.write(cr,uid,iface_ids,{"endpoint" : True} )        
        #        
        ## validate
        #validate ports
        port_ids = port_obj.search(cr,uid,[("unit_id","in",ids)])
        port_obj.do_validate(cr,uid,port_ids,context=context)                
        #validate interfaces        
        iface_obj.do_validate(cr,uid,iface_ids,context=context)
        
        #check addresses again
        for unit in self.browse(cr,uid,ids,context):                        
            for iface in unit.iface_ids:
                if iface.ipv4 and not iface.ipv4_address_id:
                    self.write(cr,uid,unit.id,{"state" : "init"})
                    raise osv.except_osv(_("Warning !"), _("No IPv4 address for interface %s of unit %s set!") % (iface.name,unit.name))
                if iface.ipv6 and not iface.ipv6_address_id:
                    self.write(cr,uid,unit.id,{"state" : "init"})
                    raise osv.except_osv(_("Warning !"), _("No IPv6 address for interface %s of unit %s set!") % (iface.name,unit.name))
                
        self.write(cr,uid,ids,{"state" : "valid"})    
        return True
    
    def do_configuration(self, cr, uid, ids, context=None):
#         job_obj = self.pool.get("posix_net.config_job")
#         job_line_obj = self.pool.get("posix_net.config_job.line")
#         job_id = job_obj.create(cr, uid, {"name" : "Config "+str(util.currentDate()), "date" : util.currentDate(), "state" : "draft"})
#         sequence = 0
#         for unit in self.browse(cr, uid, ids, context):
#             data = {
#                 "name" : unit.address_id.name,
#                 "sequence" : sequence+1,
#                 "unit_id" : unit.id,
#                 "job_id" : job_id
#             }
#             job_line_obj.create(cr ,uid, data)
#         ids = self.search(cr, uid, [("id","in",ids),("state","=","valid")]) 
#         self.do_validate(cr,uid,ids,context=context)        
#         if ids:
#             #build configuration   
#             data = self.read(cr, uid, ids, context=context)[0]                
#             datas = {
#                 "ids" : ids,
#                 "model" : self._name,
#                 "form" : data
#             }
#               
#             return {
#               "type" : "ir.actions.report.xml",
#               "report_name" : "posix_net.provisioning",
#               "datas" : datas, 
#               "nodestroy": True
#             }        
        return True
    
    def do_draft(self,cr,uid,ids,context=None):        
        self.write(cr, uid, ids, {"state" : "draft"}, context)
        return True
   
    def _is_template(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids,False)
        for unit in self.browse(cr, uid, ids, context):
            if unit.type_id.code == "template":
                res[unit.id] = True
        return res
     
    def _relids_unit_type(self, cr, uid, ids, context=None):
        unit_obj = self.pool.get("posix_net.unit")
        res = unit_obj.search(cr, uid, [("type_id", "in", ids)])
        return res
    
    def _get_info(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, False)
        
        for unit in self.browse(cr, uid, ids, context):
            address = unit.address_id
            street = address.street+"\n"
            zip_code = address.zip+" "
            city = address.city+"\n"
            number = "\n"
            if address.mobile:
                number = address.mobile+"\n\n"
            elif address.phone:
                number = address.phone+"\n\n"
            wlan_list = []
            for port in unit.port_ids:
                if port.wlan_psk and port.wlan_ssid and port.mode == "ap":
                    wlan_char = "SSID: " + port.wlan_ssid + "\n" + "Password: " + port.wlan_psk + "\n"
                    wlan_list.append(wlan_char)
            res[unit.id] = street + zip_code + city + number
            for wlan in wlan_list:
                res[unit.id] += wlan
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.has_key("name"):
            vals["subject"]=vals["name"]
        return super(posix_net_unit,self).write(cr, uid, ids, vals, context)
        
    def create(self, cr, uid, vals, context=None):
        if vals.has_key("name"):
            vals["subject"]=vals["name"]
        return super(posix_net_unit,self).create(cr, uid, vals, context=None)
    
    _name = "posix_net.unit"
    _inherits = {"password.entry" : "password_id"}
    _description = "Unit"    
    _defaults = {
        "active" : True,
        "login" : "root",
        "password" : lambda *a: util.password(),
        "state" : "draft"
    }
    
    _columns = {
        "name" : fields.char("Name", select=True, required=True,
                             help="How to define the name:\n"
                                  "Accesspoint - Name-to-Name-ap\n"
                                  "Station - Name-from-Name-st\n"
                                  "Client - Name-ap / Name-gw"),        
        "address_id" : fields.many2one("res.partner", "Partner", required=True, select=True, help="The owner of the unit"),
        "password_id" : fields.many2one("password.entry","Password", readonly=True, states={"draft" : [("readonly",False)]}, required=True, ondelete="restrict"),
        "type_id" : fields.many2one("posix_net.unit_type", "Type", required=True,
                                    states={"draft": [("readonly", False)]}, readonly=True, 
                                    help="Is necessary to select the unit type"),
        "port_ids" : fields.one2many("posix_net.port", "unit_id", "Link"),
        "service_ids" : fields.one2many("posix_net.service", "unit_id", "Service"),
        "active" : fields.boolean("Active", select=True),
        "iface_ids" : fields.one2many("posix_net.iface","unit_id","Interfaces"),
        "state" : fields.selection([("draft","Draft"),("init","Initialized"),("valid","Validated")],"State",readonly=True,select=True),
        "domain_id" : fields.many2one("posix.domain", "Domain"),
        "degrees_horiz" : fields.float("Degrees horizontal", help="Tilt up > 0\nTilt down < 0"),
        "degrees_vert" : fields.float("Degrees vertical", help="Tilt left > 0\nTilt right < 0"),
        "degrees_course" : fields.float("Degrees course", help="North = 0"),
        "lon" : fields.float("Longitude",digits_compute=dp.get_precision("Coordinates")),
        "lat" : fields.float("Latitude",digits_compute=dp.get_precision("Coordinates")),
        "height" : fields.float("Height"),
        "vlan_ids" : fields.one2many("posix_net.vlan", "unit_id", "VLAN"),
        "vlan_port_ids" : fields.one2many("posix_net.vlan_port", "unit_id", "VLAN Ports"),
        "is_template" : fields.function(_is_template, type="boolean", string="Is Template",                                      
                                         store={
                                         "posix_net.unit" : (lambda self, cr, uid, ids, c={}: ids, ['type_id'], 10),
                                         "posix_net.unit_type" : (_relids_unit_type, ["code"],10)
                                         }),                
        "info" : fields.function(_get_info, type="text", string="Info")
    }
    

class posix_net_unit_type(osv.Model):
    
    _name = "posix_net.unit_type"
    _description = "Unit Type"    
    _columns = {
        "name" : fields.char("Name", select=True, required=True),
        "code" : fields.char("Identification", select=True),
        "category_id" : fields.many2one("posix_net.unit_category", "Category", select=True),
        "description" : fields.text("Description"),
        "firmware_id" : fields.many2one("posix_net.firmware", "Firmware"),
        "area" : fields.selection([("in", "Indoor Area"), ("out", "Outdoor Area")], "Area"),
        "template_unit_id" : fields.many2one("posix_net.unit", "Unit template")
    }


class posix_net_unit_category(osv.Model):
        
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ["name", "parent_id"], context=context)
        res = []
        for record in reads:
            name = record["name"]
            if record["parent_id"]:
                name = record["parent_id"][1] + " / " + name
            res.append((record["id"], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)
    
    _name = "posix_net.unit_category"
    _description = "Unit Category"
        
    _columns = {
        "parent_id" : fields.many2one("posix_net.unit_category", "Parent", select=True,
                                      help="If you create a WLAN Router, you have to set the parent as Router:\n"
                                      + "Name: WLAN - Parent: Router"),
        "name" : fields.char("Name", select=True, required=True),
        "code" : fields.char("Code", select=True),
        "description" : fields.text("Description"),
        "complete_name": fields.function(_name_get_fnc, method=True, type="char", size=256, string="Name", store=True, select=True)
      
    }


class posix_net_iface(osv.Model):

    def onchange_dhcp(self, cr, uid, ids, dhcp):
        
        res = {
            "value" : {}
        }
        if dhcp:
            res["value"]["ipv4"] = False
            res["value"]["ipv6"] = False
            res["value"]["ipv4_address_id"] = None
            res["value"]["ipv6_address_id"] = None
        
        return res
    
    def _ipv4_mask_get(self, cr, uid, ids, field_name, arg, context=None):
        res=dict.fromkeys(ids)        
        for obj in self.browse(cr, uid, ids, context):
            parent = obj.network_id.parent_id
            if parent:
                res[obj.id]=parent.ipv4_address_id.mask
        return res
       
    def _ipv4_ip_get(self, cr, uid, ids, field_name, arg, context=None):
        res=dict.fromkeys(ids)        
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id]=obj.network_id.ipv4_address_id.ip
        return res
         
    def _ipv6_mask_get(self, cr, uid, ids, field_name, arg, context=None):
        res=dict.fromkeys(ids)        
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id]=obj.network_id.parent_id.ipv6_address_id.mask
        return res
       
    def _ipv6_ip_get(self, cr, uid, ids, field_name, arg, context=None):
        res=dict.fromkeys(ids)        
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id]=obj.network_id.ipv6_address_id.ip
        return res
   
                    
    def _search_linked_iface_ids(self,ports,iface_net,
                                 linked_iface_ids=None,
                                 linked_unit_ids=None,
                                 processed_ports=None,
                                 search_phyiface_for_port_id=False):
        if not processed_ports:
            processed_ports=set()
                   
        if ports:
            for port in ports:
                if not port.id in processed_ports:
                    processed_ports.add(port.id)
                    linked = port.linked_port_id
                    if linked:
                        child_ports = []
                        linked_iface = linked.iface_id
                        if not linked_iface:                 
                            #add linked unit      
                            linked_unit = linked.unit_id
                            if linked_unit_ids!=None:
                                if not linked_unit.id in linked_unit_ids:
                                    linked_unit_ids.append(linked_unit.id)
                            #add linked ports with no iface and network (layer2)
                            for port in linked_unit.port_ids:
                                if port.id != linked.id:
                                    child_ports.append(port)
                        #add linked ports in the same network
                        elif linked_iface.parent_id.id == iface_net.id:
                            #add linked unit                        
                            linked_unit = linked_iface.unit_id
                            if linked_unit_ids!=None:
                                if not linked_unit.id in linked_unit_ids:
                                    linked_unit_ids.append(linked_unit.id)     
                            if linked_iface_ids!=None:   
                                linked_iface_ids.append(linked_iface.id)                                                    
                            for port in linked_unit.port_ids:
                                #search for physical iface 
                                if search_phyiface_for_port_id:
                                    if port.id ==search_phyiface_for_port_id:
                                        return linked_iface
                                    elif port.tunnel_available:
                                        continue                                    
                                if port.id != linked.id:
                                    child_ports.append(port)
                        #search childs                                        
                        res = self._search_linked_iface_ids(child_ports, iface_net, linked_iface_ids, linked_unit_ids,
                                                             processed_ports,search_phyiface_for_port_id)
                        #check for result
                        if res:
                            return res
        return None
                
    
    def _linked_iface_ids(self, cr, uid, ids, field_name, arg, context=None):
        res=dict.fromkeys(ids)
        for iface in self.browse(cr, uid, ids, context):
            res_list=[]
            res[iface.id]=res_list
            #
            iface_net = iface.parent_id
            ports = iface.port_ids
            if iface_net:
                self._search_linked_iface_ids(ports,iface_net,linked_iface_ids=res_list)
        return res
        
    def _linked_unit_ids(self, cr, uid ,ids, field_name, arg, context=None):
        res=dict.fromkeys(ids)
        for iface in self.browse(cr, uid, ids, context):
            res_list=[]            
            res[iface.id]=res_list
            #
            iface_net = iface.parent_id
            ports = iface.port_ids
            if iface_net:
                self._search_linked_iface_ids(ports,iface_net,linked_unit_ids=res_list)
        return res
    
    def _linked_gw_iface_ids(self, cr, uid, ids, field_name, arg, context=None):
        res=dict.fromkeys(ids)
        for iface in self.browse(cr, uid, ids, context):
            res_list=[]            
            res[iface.id]=res_list
            #
            linked_iface_ids=[]
            iface_net = iface.parent_id
            ports = iface.port_ids
            iface_unit = iface.unit_id
            if iface_net and iface_unit:
                unit_ids = set()
                unit_ids.add(iface_unit.id)
                for iface2 in iface_unit.iface_ids:
                    if iface2.type=="gw" and iface2.id != iface.id:
                        res_list.append(iface2.id)
                
                self._search_linked_iface_ids(ports,iface_net,linked_iface_ids=linked_iface_ids)
                for iface2 in self.browse(cr, uid, linked_iface_ids):
                    if iface2.type=="gw" :
                        res_list.append(iface2.id)
                    else:
                        unit2 = iface2.unit_id
                        if unit2 and unit2.id not in unit_ids:
                            unit_ids.add(unit2.id)
                            for iface3 in unit2.iface_ids:
                                if iface3.type=="gw":
                                    #add source iface2 as gw
                                    res_list.append(iface2.id)                      
        return res
     
    def _linked_services(self,cr,uid,iface,service_type,context=None):
        res = []
        id_set = set()
        for iface in iface.linked_iface_ids:
            for service in iface.service_ids:
                if service.type_id.name == service_type:
                    if not service.id in id_set:
                        id_set.add(service.id)
                        res.append(service)
        return res
    
    def _linked_service_ifaces(self, cr, uid, iface, service, linked_ifaces_ids=None, context=None):
        res = []
        if not linked_ifaces_ids:
            linked_ifaces_ids=[x.id for x in iface.linked_iface_ids]
        for service_iface in service.iface_ids:
            if service_iface.id in linked_ifaces_ids:
                res.append(service_iface)
        return res     
    
    def _linked_services_ifaces(self,cr,uid, iface, services, linked_ifaces_ids=None, context=None):
        res=[]
        if not linked_ifaces_ids:
            linked_ifaces_ids=[x.id for x in iface.linked_iface_ids]
        for service in services:
            res.extend(self._linked_service_ifaces(cr, uid, iface, service, linked_ifaces_ids, context))
        return res
    
         
    def _dns_iface_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)        
        for iface in self.browse(cr, uid, ids, context):
            dns_services = iface.dns_service_ids
            if not dns_services:
                dns_services = self._linked_services(cr, uid, iface, "dns", context)
            #
            linked_services_ifaces = self._linked_services_ifaces(cr,uid,iface,dns_services,context=context)
            res[iface.id]=[x.id for x in linked_services_ifaces]
        return res  
    
    def copy(self, cr, uid, oid, default=None, context=None):                
        
        if not default:
            default = {}
        if not default.has_key("network_id"):
            default["network_id"]=None
        if not default.has_key("port_ids"):
            default["port_ids"]=[]
        if not default.has_key("service_ids"):
            default["service_ids"]= []
        if not default.has_key("dns_service_ids"):
            default["dns_service_ids"]=None
        res = super(posix_net_iface,self).copy(cr,uid,oid,default,context)
        
        return res
    
    def name_get(self, cr, uid, ids, context=None):        
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ["unit_id", "name"], context=context)
        res = []
        for record in reads:
            tokens = []            
            if record["unit_id"]:
                tokens.append(record["unit_id"][1])
            tokens.append(record["name"])            
            res.append((record["id"], " / ".join(tokens)))
        return res
  
    def do_validate(self,cr,uid,ids,context=None):        
        network_obj = self.pool.get("posix_net.network")
        #validate network objects an ip addresses
        network_ids = [o.network_id.id for o in self.browse(cr,uid,ids)]
        network_obj.do_validate(cr,uid,network_ids,context=context)
        
        for iface in self.browse(cr, uid, ids, context):
            parent_network = iface.parent_id
            if not parent_network.is_template:
                ip_name = []
                if iface.unit_id:
                    ip_name.append(iface.unit_id.name)
                if iface.name:
                    ip_name.append(iface.name)
                ip_name = " / ".join(ip_name)
                # update ipv4 name
                if iface.ipv4_address_id and iface.ipv4_address_id.name != ip_name:
                    self.pool.get("posix_net.net_ipv4_address").write(cr,uid,iface.ipv4_address_id.id,{ "name" : ip_name } )
                # update ipv6 name
                if iface.ipv6_address_id and iface.ipv6_address_id.name != ip_name:
                    self.pool.get("posix_net.net_ipv6_address").write(cr,uid,iface.ipv6_address_id.id,{ "name" : ip_name } )
                    
                

    def onchange_network(self, cr, uid, ids, network_id, context=None):        
        res = {}
        domain_value = []
        domain = { "ipv4_address_id"  : domain_value }
        if network_id:
            network = self.pool.get("posix_net.network").browse(cr, uid, network_id)
            domain_value.append(("parent_id", "=", network.ipv4_address_id.id))                       
        res["domain"] = domain
        return res
    
    def _info(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            info = []
            if obj.ipv4_address_id:
                info.append(obj.ipv4_address_id.ip)
            if obj.ipv6_address_id:
                info.append(obj.ipv6_address_id.ip)
            if obj.dhcp:
                info.append(_("DHCP"))
            res[obj.id]="\n".join(info)
        return res
        
    _name = "posix_net.iface"
    _inherits = {"posix_net.network" : "network_id"}
    _description = "Unit Interface"    
    _columns = {                        
        "code" : fields.char("Iface"),
        "unit_id" : fields.many2one("posix_net.unit","Unit",select=True,ondelete="cascade",required=True),
        "network_id" : fields.many2one("posix_net.network", "Network", select=True, required=True, ondelete="cascade"),
        "ipv4_ip" : fields.function(_ipv4_ip_get, type="char", size=16, method=True,string="IP"),
        "ipv4_mask" : fields.function(_ipv4_mask_get, type="integer", method=True,string="Mask"),
        "ipv6_ip" : fields.function(_ipv6_ip_get, type="char", size=64, method=True,string="IP"),
        "ipv6_mask" : fields.function(_ipv4_mask_get, type="integer", method=True,string="Mask"),
        "gw_iface_ids" : fields.function(_linked_gw_iface_ids,type="many2many",obj="posix_net.iface",
                                         string="Linked Gateways",help="Linked Gateway Interface"),
        "linked_iface_ids" : fields.function(_linked_iface_ids,type="many2many",obj="posix_net.iface",
                                             string="Linked Interface",help="Linked Interfaces in one network segment"),
        "linked_unit_ids" : fields.function(_linked_unit_ids,type="many2many",obj="posix_net.unit",
                                             string="Linked Units", help="All Units in which are in one network segment"),
        "type" : fields.selection([("site","Site"), ("gw","Gateway"), ("link","Link")], "Type"),
        "qos_profile_id" : fields.many2one("posix_net.qos_profile", "QoS Profile"),
        "port_ids" : fields.one2many("posix_net.port","iface_id","Ports"),
        "service_ids" : fields.many2many("posix_net.service", "posix_net_service_iface_rel", "iface_id", "service_id", "Services"),
        "dns_service_ids" : fields.many2many("posix_net.service","posix_net_iface_dns_service_rel","iface_id","service_id",string="DNS",
                                              domain=[('type_id.name','=','dns')]),
        "dns_iface_ids" : fields.function(_dns_iface_ids,type="many2many",obj="posix_net.iface",string="Linked DNS Interfaces"),
        "dhcp" : fields.boolean("DHCP"),
        "parent_ipv4_related" : fields.related("parent_id", "ipv4_address_id", type="many2one", obj="posix_net.net_ipv4_address", string="Network Address", readonly=True),
        "parent_ipv6_related" : fields.related("parent_id", "ipv6_address_id", type="many2one", obj="posix_net.net_ipv6_address", string="Network Address", readonly=True),
        "info" : fields.function(_info,type="char",string="Info")
     }    
    _defaults = {
        "endpoint" : True
    }
    
    
class posix_net_port(osv.Model):
    
    def copy(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}        
        default["linked_port_id"]=None
        default["linked_port_ids"]=None
        if not default.has_key("wlan_master_port_id"):
            default["wlan_master_port_id"] = None
        if not default.has_key("wlan_slave_ids"):
            default["wlan_slave_ids"] = None
        if not default.has_key("wlan_channel_id"):
            default["wlan_channel_id"] = None
        if not default.has_key("iface_id"):
            default["iface_id"] = None
        
        if oid:
            port = self.browse(cr, uid, oid, context)
            unit = port.unit_id
            if not default.has_key("sequence"):
                port_num = 0
                if unit:
                    for cur_port in unit.port_ids:
                        port_num = max(port_num,cur_port.sequence)
                    port_num+=1
                    default["sequence"]=port_num
                default["name"]=_("Port %s") % str(port_num)
        
        res = super(posix_net_port,self).copy(cr,uid,oid,default,context)
        return res
     
    def _possible_link_port_ids_search(self, cr, uid, port, port_type, mode, iface, context=None):
        network = iface and iface.parent_id or None        
        if mode and port_type:
            unit = port and port.unit_id or None
            unit_id = context and context.get("unit_id") or None
            if unit_id:
                unit = self.pool.get("posix_net.unit").browse(cr,uid,unit_id)
            #
            address = unit and unit.address_id or None
            #    
            if network:
                if mode == "client":
                    if network.private and address:
                        return self.search(cr, uid, [("unit_id.address_id","=", address.id), ("mode","=","ap"), ("type_id.category_ids", "in", [x.id for x in port_type.category_ids])])
                    return self.search(cr, uid, [("mode","=","ap"),("type_id.category_ids", "in", [x.id for x in port_type.category_ids])])#("iface_id.network_id.parent_id","=",network.id),
                elif mode == "link":
                    if not address:
                        return self.search(cr, uid, [("iface_id.network_id.parent_id","=",network.id),("mode","=","link"),("type_id.category_ids", "in", [x.id for x in port_type.category_ids])])
            if mode == "link" and address:
                return self.search(cr, uid, [("unit_id.address_id","=",address.id),("mode","=","link"),("type_id.category_ids", "in", [x.id for x in port_type.category_ids])])
            elif mode == "client":
                if port_type.tunnel_available:      
                    return self.search(cr, uid, [("type_id.tunnel_available","=",True),("mode","=","ap"),("type_id.category_ids", "in", [x.id for x in port_type.category_ids])])
                elif port_type.wlan_available:
                    return self.search(cr, uid, [("type_id.wlan_available","=",True),("mode","=","ap"),("type_id.category_ids", "in", [x.id for x in port_type.category_ids])])
                      
        return []
    
    def _possible_link_port_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id]=self._possible_link_port_ids_search(cr, uid,obj, obj.type_id, obj.mode, obj.iface_id, context=context)             
        return res
    
    def _get_possible_master_ports(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            if obj.unit_id:
                res[obj.id]=self.search(cr, uid, [("unit_id.address_id", "=", obj.unit_id.address_id.id),("wlan_master","=",True)])                         
        return res
            
    def _get_port_type(self,cr,uid,unit,port_name,context=None):
        if unit:
            unit_type = unit.type_id
            if unit_type:
                port_type_obj = self.pool.get("posix_net.unit_type")
                port_type_ids = port_type_obj.search(cr,uid,[("name","=",port_name)])
                if port_type_ids:
                    return port_type_obj.browse(cr,uid,port_type_ids[0])
        return None
     

    def onchange_autoconfig(self,cr,uid,ids,auto_config,auto_config_old, unit_id, port_name, sequence, port_mode, port_type_id,
                            port_linked_port_id, wlan_ssid, encrypt, auth_mode, wlan_psk, wlan_channel_id,
                            wds, shifting, bandwidth, txpower, airmax,
                            master, master_port_id):
                
        res_value = {
            "value" : { "wlan_auto_config_old" : auto_config }
        }
        res = {"value" : res_value }
        
        if (auto_config != auto_config_old):                                   
            unit = None
            if unit_id:
                unit = self.pool.get("posix_net.unit").browse(cr, uid, unit_id)
            
                address = unit.address_id
                unit_name = unit.name
                port_type = self.pool.get("posix_net.port_type").browse(cr, uid, port_type_id)
                linked_port = port_linked_port_id and self.browse(cr, uid, port_linked_port_id) or None
                master_port = master_port_id and self.browse(cr, uid, master_port_id) or None
                res_value.update(self._wlan_auto_config_do(cr, uid, True, address, unit_name, sequence and str(sequence) or "", port_mode, 
                                           port_type, linked_port, wlan_ssid, encrypt, auth_mode, wlan_psk, wlan_channel_id,
                                           wds, shifting, bandwidth, txpower, airmax,
                                           master, master_port))
            else:
                port_type = self.pool.get("posix_net.port_type").browse(cr, uid, port_type_id)
                linked_port = port_linked_port_id and self.browse(cr, uid, port_linked_port_id) or None
                master_port = master_port_id and self.browse(cr, uid, master_port_id) or None
                res_value.update(self._wlan_auto_config_do(cr, uid, True, None, None, sequence and str(sequence) or "", port_mode, 
                                           port_type, linked_port, wlan_ssid, encrypt, auth_mode, wlan_psk, wlan_channel_id, 
                                           wds, shifting, bandwidth, txpower, airmax,
                                           master, master_port))
          
        return res
        
    def onchange_port(self, cr, uid, ids, port_type_id, mode, iface_id, context=None):      
        res_value = {
            "wlan_available" : False,
            "tunnel_available" : False,
            "iface_name" : None,
            "wlan_airmax" : False,
            "wlan_shifting_available" : False
        }
        res = {
           "value" : res_value
        }
        
        port = ids and self.browse(cr, uid, ids[0]) or None
        iface = iface_id and self.pool.get("posix_net.iface").browse(cr,uid,iface_id) or None
        if iface:
            res_value["iface_name"]=iface.name
        if context and context.get("unit_id"):
            res_value["unit_id"] = context["unit_id"]
        res_value["wlan_available"] = False
        res_value["tunnel_available"] = False

        port_type = port_type_id and self.pool.get("posix_net.port_type").browse(cr,uid,port_type_id) or None       
        if port_type:            
            res_value["wlan_available"] = port_type.wlan_available
            res_value["tunnel_available"] = port_type.tunnel_available
            res_value["wlan_airmax"] = port_type.wlan_air_max_available
            res_value["wlan_shifting_available"] = port_type.wlan_channel_shift_available
        
            if port_type.wlan_available:
                res_value["wlan_available"] = True
            else:
                res_value["wlan_available"] = False
                
            if port_type.tunnel_available:
                res_value["tunnel_available"] = True
            else:
                res_value["tunnel_available"] = False
            
        if port_type_id and mode:
            res_value["mode"] = mode
            if iface:                
                res_value["possible_link_port_ids"]=self._possible_link_port_ids_search(cr,uid,port,port_type,mode,iface)
                
        else:            
            res_value["mode"]=None
            res_value["linked_port_id"]=None
        return res
        
    def _port_name(self, cr, uid, ids, field_name, arg, context=None):
        cr.execute(
            "SELECT p.id, p.port, p.name, i.code, t.code  FROM posix_net_port p "
            " LEFT JOIN posix_net_iface i ON i.id = p.iface_id " 
            " LEFT JOIN posix_net_port_type t ON t.id = p.type_id "
            " WHERE p.id IN %s ", 
            (tuple(ids),)           
        )
        
        res = dict.fromkeys(ids)
        for port_id, port, port_name, iface_name, port_type_code in cr.fetchall():
            if port_name:
                res[port_id]=port_name
            elif port_type_code:
                res[port_id]="%s%s" % (port_type_code,port or 0)
            elif iface_name:
                res[port_id]=iface_name
        return res
            
    def _port_path(self, cr, uid, ids, context=None):
        cr.execute(
        "SELECT p.id, p.port, p.name, u.id, u.name, i.code, t.code  FROM posix_net_port p "
        " LEFT JOIN posix_net_unit u ON u.id = p.unit_id " 
        " LEFT JOIN posix_net_iface i ON i.id = p.iface_id " 
        " LEFT JOIN posix_net_port_type t ON t.id = p.type_id "
        " WHERE p.id IN %s ", 
        (tuple(ids),)           
        )
        cur_unit_id = context.get("unit_id")
        res = dict.fromkeys(ids)
        for port_id, port, port_name, unit_id, unit_name, iface_name, port_type_code in cr.fetchall():
            name = []
            if cur_unit_id != unit_id and unit_name:
                name.append(unit_name)
              
            if iface_name:
                name.append(iface_name)
                
            if port_name:
                name.append(port_name)
            elif port_type_code:
                name.append("%s%s" % (port_type_code,port or 0))
            else:
                name.append(str(port or 0))
                
            res[port_id] = "-".join(name)
        return res
        
    def name_get(self, cr, uid, ids, context=None):
        res = []
        if ids:
            names = self._port_path(cr, uid, ids, context=context)
            for oid in ids:
                res.append((oid,names[oid]))
        return res
    
    def _tunnel_auto_config_do(self, cr, uid, force,                            
                              mode, linked_port, tunnel_name, tunnel_password,context=None):
        
        res = {}
        if mode == "client":
            if linked_port:
                res["tunnel_name"]=linked_port.tunnel_name
                res["tunnel_password"]=linked_port.tunnel_password 
        if mode == "ap":
            if not tunnel_password:                
                res["tunnel_password"]=util.password(32)   
        return res 
    
    def _wlan_auto_config_do(self, cr, uid, force,
                              address, unit_name, port_name,
                              mode, port_type, linked_port, 
                              ssid, encrypt, auth,  psk, channel, wds,
                              channel_shifting, channel_width, txpower, airmax,
                              master, master_port,       
                              context=None):
        res = {}
        
        #check config against port type
        if port_type:
            if txpower > port_type.wlan_max_txpower or not txpower:
                res["wlan_txpower"]=port_type.wlan_max_txpower
                
            if channel_width > port_type.wlan_max_bandwidth or not channel_width:
                res["wlan_bandwidth"]=port_type.wlan_max_bandwidth or None
            
            if not port_type.wlan_shifting_available and channel_shifting:                              
                res["wlan_shifting"]=False
        else:
            res["wlan_txpower"]=None
            res["wlan_bandwidth"]=None
            res["wlan_shifting"]=False

        #client config
        if mode == "client":           
            if linked_port:             
                if linked_port.wlan_psk == False:
                    linked_port.wlan_psk = None
                res["wlan_psk"]=linked_port.wlan_psk
                res["wlan_encrypt"]=linked_port.wlan_encrypt
                res["wlan_auth_mode"]=linked_port.wlan_auth_mode                
                res["wlan_channel_id"]=linked_port.wlan_channel_id.id or None
                res["wlan_ssid"]=linked_port.wlan_ssid or None
                res["wlan_ssid_hidden"]=linked_port.wlan_ssid_hidden or False 
                res["wlan_bandwidth"]=linked_port.wlan_bandwidth or None      
                res["wlan_shifting"]=linked_port.wlan_shifting or False
                res["wlan_wds"]=linked_port.wlan_wds
                res["wlan_airmax"] = linked_port.wlan_airmax
                return res
        #accesspoint config   
        elif mode == "ap":
            
            if port_type.wlan_available:
                if (not channel or force) and address:
                    used_channels = []
                    ports = self.browse(cr,uid,self.search(cr, uid, [("unit_id.address_id","=",address.id),("wlan_channel_id","!=","False")]))
                    for port in ports:
                        if port.wlan_channel_id:
                            used_channels.append(port.wlan_channel_id.id)
                    res["wlan_channel_id"]=self.pool.get("posix_net.wlan_channel")._get_preferred_channel_id(cr,uid,port.type_id.allowed_channel_ids, used_channels,context)
            elif channel:
                res["wlan_channel_id"]=None      
                             
            if unit_name and (not ssid or force):
                if not master or not ssid:            
                    if port_name: 
                        res["wlan_ssid"]=("%s-%s" % (unit_name,port_name))
                    else:
                        res["wlan_ssid"]=unit_name
            if not auth:
                res["wlan_auth_mode"]="psk"
                auth="psk"
            if auth == "psk":
                key_len = 32
                if port_type.key_len != 0:
                    key_len = port_type.key_len
                if not psk or key_len < len(psk):                         
                    res["wlan_psk"]=util.password(key_len)
            if not encrypt:
                res["wlan_encrypt"]="wpa"   
            #master configuration override            
            if not master and master_port:
                res["wlan_auth_mode"]=master_port.wlan_auth_mode
                res["wlan_psk"]=master_port.wlan_psk
                res["wlan_ssid"]=master_port.wlan_ssid
            #
            return res    
            
        
#        res["wlan_psk"]=None
#        res["wlan_encrypt"]=None
#        res["wlan_auth_mode"]=None
#        res["wlan5_channel"]=None
#        res["wlan2_4_channel_id"]=None
#        res["wlan_ssid"]=None
#        res["wlan_ssid_hidden"]=None     
#        res["wlan_bandwidth"]=None      
#        res["wlan_shifting"]=False    
#        res["wlan_ssid"]=None
#        res["wlan_wds"]=False
#        res["wlan_airmax"]=False
        return res
   
      
    def _destination_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)        
        for obj in self.browse(cr, uid, ids, context):
            res_value=[]
            res[obj.id]=res_value
            if obj.linked_port_id:
                res_value.append(obj.linked_port_id.id)
            for linked in obj.linked_port_ids:
                res_value.append(linked.id)            
        return res
    
    def _wlan_mapped_channel(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        line_obj = self.pool.get("posix_net.frequency_mapping_line")
        for obj in self.browse(cr, uid, ids, context):
            channel = obj.wlan_channel_id
            port_type = obj.type_id
            bandwidth = obj.wlan_bandwidth
            if channel and port_type:
                channel = line_obj.mapping_channel_get(cr,uid,bandwidth,channel,port_type.id,obj.wlan_shifting)
                res[obj.id]=channel.id
        return res
    
    def _relids_posix_net_port(self,cr,uid,ids,context=None):
        res = list(ids)
        cr.execute("SELECT p.id FROM posix_net_port AS p WHERE linked_port_id IN %s GROUP BY 1",(tuple(ids),))
        for row in cr.fetchall():
            res.append(row[0])
        return res
    
    def _tunnel_phyiface_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        iface_obj = self.pool.get("posix_net.iface")
        for port in self.browse(cr, uid, ids, context):
            linked_port = port.linked_port_id
            if linked_port:
                tunnel_iface_id=linked_port.tunnel_iface_id
                if tunnel_iface_id:
                    res[port.id]=tunnel_iface_id.id
                else:
                    port_iface = port.iface_id
                    if port_iface and port.mode == "client" and port.tunnel_available:
                        unit = port.unit_id
                        for iface in unit.iface_ids:
                            if iface.id != port_iface.id:
                                iface = iface_obj._search_linked_iface_ids(unit.port_ids,iface.network_id.parent_id,
                                                                   search_phyiface_for_port_id=linked_port.id)
                                res[port.id]=iface and iface.id or None
                
        return res
                
    
    def do_validate(self,cr,uid,ids,deep=True,context=None):
        #validate links
        linked_accesspoint_ids = []
        for port in self.browse(cr,uid,ids,context):
            mode = port.mode
            if mode=="ap" and port.linked_port_id:
                self.write(cr, uid, port.id, {"linked_port_id" : None}, context)                
            elif mode=="link":
                #validate linked port
                linked_port = port.linked_port_id
                if linked_port:                    
                    linked_linked = linked_port.linked_port_id
                    if not linked_linked or linked_linked.id != port.id:
                        self.write(cr, uid, linked_port.id, {"linked_port_id":port.id}, context)                
                
                #validate links             
                peer = None
                delete_links = []
                for link in port.linked_port_ids:
                    if link.mode != "link":
                        delete_links.append(link.id)
                    elif not peer:
                        peer = link
                        if not port.linked_port_id or port.linked_port_id.id != peer.id:                                                                        
                            self.write(cr, uid, port.id, { "linked_port_id" : peer.id }, context)
                    else:
                        delete_links.append(link.id)                               
                if delete_links:         
                    self.write(cr, uid, delete_links, {"linked_port_id" : None}, context)
                    
            elif mode=="client":
                link = port.linked_port_id
                if link:
                    if link.mode!="ap":
                        self.write(cr, uid, port.id, {"linked_port_id" : None}, context)
                    elif not link.id in linked_accesspoint_ids:
                        linked_accesspoint_ids.append(link.id)
                
        
        #validate accesspoints before other                
        if linked_accesspoint_ids and deep:                      
            self.do_validate(cr, uid, linked_accesspoint_ids, deep=False, context=context)        

        #auto config
        for port in self.browse(cr,uid,ids,context):
            mode = port.mode
            if port.id in linked_accesspoint_ids:
                continue
            
            auto_config = None
            linked_port = port.linked_port_id
            mode = port.mode
             
            if port.tunnel_available:
                tunnel_name = port.tunnel_name
                tunnel_password = port.tunnel_password
                auto_config = self._tunnel_auto_config_do(cr, uid, False, mode, linked_port,
                                                           tunnel_name, tunnel_password, context)
                                    
            elif port.wlan_auto_config:                                   
                address = port.unit_id and port.unit_id.address_id or None
                unit_name = port.unit_id and port.unit_id.name or None
                port_name = port.sequence and str(port.sequence) or ""                
                port_type = port.type_id
                ssid = port.wlan_ssid
                encrypt=port.wlan_encrypt
                auth=port.wlan_auth_mode
                psk=port.wlan_psk
                channel=port.wlan_channel_id
                wds=port.wlan_wds
                channel_shifting=port.wlan_shifting
                channel_width=port.wlan_bandwidth 
                txpower=port.wlan_txpower          
                airmax=port.wlan_airmax                   
                master=port.wlan_master                
                master_port=port.wlan_master_port_id

                auto_config = self._wlan_auto_config_do(cr, uid, False, address, unit_name, port_name, mode, 
                                           port_type, linked_port, ssid, encrypt, auth, psk, channel, 
                                           wds, channel_shifting, channel_width, txpower, airmax,
                                           master, master_port,
                                           context)
                                
            #save autoconfig
            if auto_config:
                self.write(cr, uid, [port.id], auto_config, context)           

            #validate accesspoints childs   
            if deep and mode == "ap":
                self.do_validate(cr, uid, [l.id for l in port.linked_port_ids], deep=False, context=context)
                self.do_validate(cr, uid, [s.id for s in port.wlan_slave_ids], deep=False, context=context)

    _name = "posix_net.port"
    _description = "Port"
    _columns = {
        "sequence" : fields.integer("Sequence", required=True),
        "port" : fields.integer("Port",select=True,required=True),
        "name" : fields.char("Device"),
        "port_name" : fields.function(_port_name,type="char",string="Device",store=False),
        "enabled" : fields.boolean("Enabled"),
        "unit_id" :  fields.many2one("posix_net.unit", "Unit", select=True, ondelete="cascade"),
        "iface_id" : fields.many2one("posix_net.iface","Interface",select=True),
        "iface_name" : fields.related("iface_id", "name", type="char", string="Interface",readonly=True),
        "type_id" : fields.many2one("posix_net.port_type", "Type", select=True, ondelete="restrict"),
        "linked_port_id" : fields.many2one("posix_net.port", "Link", help="The connection of two routers",ondelete="set null"),
        "linked_port_ids" : fields.one2many("posix_net.port","linked_port_id","Links",help="Links from other to this port"),
        "destination_ids" : fields.function(_destination_ids,type="many2many",obj="posix_net.port", readonly=True, string="Linked and Linked To Ports"),    
        "possible_link_port_ids" : fields.function(_possible_link_port_ids, type="many2many", obj="posix_net.port", method=True, readonly=True, string="Possible Link Ports"),   
        "mode" : fields.selection(selection=[("link", "Link"), ("client", "Client"), ("ap", "Accesspoint")], string="Mode"),
        "wlan_auto_config_old" : extfields.duplicate("wlan_auto_config","Auto Configuration (Old)",type="boolean"),
        "wlan_auto_config" : fields.boolean("Auto Configuration"),       
        "wlan_wds" : fields.boolean("WDS"),
        "wlan_ssid" : fields.char("SSID",size=32),                
        "wlan_ssid_hidden" : fields.boolean("Hidden SSID"),               
        "wlan_encrypt" : fields.selection([("wpa", "WPA")],"Encryption"),
        "wlan_auth_mode" :  fields.selection([("psk", "Preshared Key"), ("radius", "RADIUS")], "Authentication"),
        "wlan_psk" : fields.char("WLAN PSK"),
        "wlan_txpower" : fields.integer("TX Power"),
        "wlan_bandwidth" : fields.selection([(5,"5 Mhz"),(10,"10 Mhz"),(20,"20 Mhz"), (30, "30 Mhz"), (40,"40 Mhz")],"Channel Bandwidth"),
        "wlan_shifting" : fields.boolean("Channel Shifting"),
        "wlan_shifting_available" : fields.related("type_id","wlan_channel_shift_available",type="boolean", string="WLAN Channel Shifting available", readonly=True),
        "radius_username" : fields.char("Username"),
        "radius_password" : fields.char("Password"),
        "radius_service_id" : fields.many2one("posix_net.service", "Radius Service",domain=[("type_id.name","=","radius")]),
        "tunnel_name" : fields.char("Name"),
        "tunnel_password" : fields.char("Password"),
        "tunnel_available" : fields.related("type_id","tunnel_available",type="boolean", string="Tunnel Available", readonly=True),
        "tunnel_phyiface_id" : fields.function(_tunnel_phyiface_id,type="many2one",obj="posix_net.iface", method=True, readonly=True, string="Physical Remote Port on Server"),
        "tunnel_iface_id" : fields.many2one("posix_net.iface", "Interface"),
        "info" : fields.text("Info", readonly=True),
        "wlan_airmax" : fields.boolean("AirMax"),
        "wlan_airmax_available" : fields.related("type_id","wlan_air_max_available",type="boolean", string="WLAN AirMax available", readonly=True),  
        "state_unit" : fields.related("unit_id", "state", type="selection", selection=[("draft","Draft"),("init","Initialized"),("valid","Validated")], string="States", readonly=True),
        "wlan_master" : fields.boolean("Master"),
        "wlan_master_port_id" : fields.many2one("posix_net.port", "Master Link",select=True),
        "wlan_slave_ids" : fields.one2many("posix_net.port","wlan_master_port_id","WLAN Slaves"),                    
        "possible_master_port_ids" : fields.function(_get_possible_master_ports, type="many2many", obj="posix_net.port", method=True, string="Possible master ports"),
        "wlan_channel_id" : fields.many2one("posix_net.wlan_channel", "Frequency", ondelete="restrict"),
        "wlan_mapped_channel_id" : fields.function(_wlan_mapped_channel,type="many2one",obj="posix_net.wlan_channel",readonly=True,string="Frequency Used"),
        "wlan_available" : fields.related("type_id","wlan_available",type="boolean", string="WLAN Available", readonly=True),
        "rel_allowed_channel_ids" : fields.related("type_id", "allowed_channel_ids", type="many2many", readonly=True, relation="posix_net.port_type", string="Channels"),
        "priority" : fields.selection([("1","Low"),("5","Normal"),("9","High")],"Priority")
     }
    _order = "unit_id, sequence"
    _defaults = {
        "enabled" : True,
        "port" : 0,
        "sequence" : 10
    }


class posix_net_port_type(osv.Model):
    
    def name_get(self, cr, uid, ids, context=None):             
        if not len(ids):
            return []        
        reads = self.read(cr, uid, ids, ["name","category_names"], context=context)
        res = []        
        for record in reads:            
            tokens=[]       
            tokens.append(record["name"])
            if record["category_names"]:
                tokens.append(record["category_names"])
            res.append((record["id"], " / ".join(tokens)))
        return res
        
    def _category_names_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        if not len(ids):
            return []
        category_obj = self.pool.get("posix_net.port_category")
        reads = self.read(cr, uid, ids, ["category_ids"], context=context)
        res = []        
        for record in reads:
            port_category_names = category_obj.read(cr,uid,record["category_ids"], ["name"],context=context)
            tokens=[]            
            for port_category_name in port_category_names: 
                tokens.append(port_category_name["name"])                
            res.append((record["id"], " / ".join(tokens)))        
        return dict(res)

    _name = "posix_net.port_type"
    _description = "Port Type"
    
    _columns = {
        "name" : fields.char("Name", select=True, required=True),
        "code" : fields.char("Device", select=True),
        "category_ids" : fields.many2many("posix_net.port_category", "posix_net_port_type_category_rel", "type_id", "category_id", "Category", select=True, required=1, help="This sets, if the category is a WLAN or a LAN Port"),
        "category_names" : fields.function(_category_names_get_fnc, method=True, type="char", size=256, string="Category"),
        "ipv4_available" : fields.boolean("IPv4 Available"),
        "ipv6_available" : fields.boolean("IPv6 Available"),
        "tunnel_available" : fields.boolean("Tunnel Available"),
        "wlan_available" : fields.boolean("WLAN Available"),   
        "wlan_max_txpower" : fields.integer("TX Power"),
        "wlan_max_bandwidth" : fields.selection([(5,"5 Mhz"),(10,"10 Mhz"),(20,"20 Mhz"),(30, "30 Mhz"),(40,"40 Mhz")],"Channel Bandwidth"),
        "wlan_shifting_available" : fields.boolean("Channel Shifting Available"),
        "port_ids" : fields.one2many("posix_net.port", "type_id", "Ports", readonly=True),
        "wlan_air_max_available" : fields.boolean("WLAN AirMax Available"),
        "wlan_channel_shift_available" : fields.boolean("WLAN Channel Shifting Available"),
        "tunnel_type" : fields.selection([("vtun", "VTUN"), ("l2tp", "L2TP"), ("vpls", "VPLS")], "Type"),
        "allowed_channel_ids" : fields.many2many("posix_net.wlan_channel", "posix_net_wlan_channel_port_rel", "type_id", "channel_id", "Allowed Channels"),
        "key_len" : fields.integer("Key length")
    }


class posix_net_frequency_mapping(osv.Model):
    _name = "posix_net.frequency_mapping"
    _description = "Frequency Mapping"    
    _columns = {
        "name" : fields.char("Name",select=True,required=True),
        "port_type_ids" : fields.many2many("posix_net.port_type","posix_net_frequency_mapping_port_type_rel","frequency_mapping_id","port_type_id",string="Port Types"),
        "line_ids" : fields.one2many("posix_net.frequency_mapping_line", "frequency_mapping_id", string="Mapping Lines"),
        "sequence" : fields.integer("Sequence")        
    }
    _order = "sequence asc"


class posix_net_frequency_mapping_line(osv.Model):    
    def mapping_get(self, cr, uid, bandwidth, frequency, port_type_id, shifting=False, context=None):
        cr.execute("SELECT l.id FROM posix_net_frequency_mapping_line AS l "
                   " INNER JOIN posix_net_frequency_mapping AS m ON m.id = l.frequency_mapping_id "
                   " INNER JOIN posix_net_frequency_mapping_port_type_rel AS r ON r.frequency_mapping_id = m.id AND r.port_type_id = %s "
                   " WHERE l.bandwidth = %s AND l.channel = %s AND shifting = %s " 
                   " ORDER BY m.sequence ", (port_type_id,bandwidth,frequency,shifting))
        #self.search(cr,uid,[("bandwidth","=",bandwidth),("frequency","=",frequency),("shifting","=",shifting),("frequency_mapping_id.port_type_ids","in",[port_type_id])])
        ids = [r[0] for r in cr.fetchall()]
        for line in self.browse(cr, uid, ids, context):
            return line.name
        return None        
    
    def mapping_channel_get(self, cr, uid, bandwidth, channel, port_type_id, shifting=False, context=None):
        if not bandwidth:
            bandwidth=40            
        cr.execute("SELECT l.id FROM posix_net_frequency_mapping_line AS l "
                   " INNER JOIN posix_net_frequency_mapping AS m ON m.id = l.frequency_mapping_id "
                   " INNER JOIN posix_net_frequency_mapping_port_type_rel AS r ON r.frequency_mapping_id = m.id AND r.port_type_id = %s "
                   " WHERE l.bandwidth = %s AND l.channel = %s AND shifting = %s " 
                   " ORDER BY m.sequence ", (port_type_id,bandwidth,channel.frequency,shifting))
        #self.search(cr,uid,[("bandwidth","=",bandwidth),("frequency","=",frequency),("shifting","=",shifting),("frequency_mapping_id.port_type_ids","in",[port_type_id])])
        ids = [r[0] for r in cr.fetchall()]
        for line in self.browse(cr, uid, ids, context):
            channel_ids = channel._table.search(cr,uid,[("name","=",line.name)])
            if channel_ids:
                return channel._table.browse(cr,uid,channel_ids[0],context)            
        return channel
    
    _name = "posix_net.frequency_mapping_line"
    _description = "Frequency Mapping Line"    
    _columns = {
        "name" : fields.char("Mapping",size=16,select=True,required=True),
        "frequency_mapping_id" : fields.many2one("posix_net.frequency_mapping","Frequency Mapping",select=True,required=True,ondelete="cascade"),        
        "channel" : fields.integer("Channel",select=True,required=True),
        "bandwidth" : fields.integer("Bandwidth",select=True,required=True),
        "shifting" : fields.boolean("Channel Shifting",select=True,required=True)
    }
    _order = "frequency_mapping_id,bandwidth,channel asc"


class posix_net_port_category(osv.Model):
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ["name", "parent_id"], context=context)
        res = []
        for record in reads:
           
            name = record["name"]
            if record["parent_id"]:
                name = record["parent_id"][1] + " / " + name
            res.append((record["id"], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)
    
    _name = "posix_net.port_category"
    _description = "Port Category"
    
    _columns = {
        "parent_id" : fields.many2one("posix_net.port_category", "Parent", select=True,
                                      help="If you create a WLAN Port, you have to set the parent as Ethernet:\n"
                                      + "Name: WLAN - Parent: Ethernet"),
        "name" : fields.char("Name", select=True, required=True),
        "code" : fields.char("Code", select=True),
        "complete_name": fields.function(_name_get_fnc, method=True, type="char", size=256, string="Name", store=True, select=True),
        "type_ids" : fields.many2many("posix_net.port_type", "posix_net_port_type_category_rel", "category_id", "type_id", "Port Types")
    }    

class posix_net_service(osv.Model):
    
    def copy(self, cr, uid, oid, default=None, context=None):
        if not default.get("iface_ids"):
            default["iface_ids"] = []
        
        res = super(posix_net_service, self).copy(cr, uid, oid, default, context)
        return res
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ["name", "unit_id"], context=context)
        res = []
        for record in reads:
            name = record["name"]
            if record["unit_id"]:
                name = record["unit_id"][1] + " / " + name
                res.append((record["id"], name))
        return res
    
    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=None)        
        return dict(res)

    _name="posix_net.service"
    _description="Service"    
    _columns = {
        "name" : fields.char("Name", required=True, select=True),
        "complete_name" : fields.function(_name_get_fnc, method=True, type="char", size=256, string="Name", store=True, select=True),
        "unit_id" : fields.many2one("posix_net.unit", "Unit", select=True,ondelete="cascade"),
        "iface_ids" : fields.many2many("posix_net.iface", "posix_net_service_iface_rel", "service_id", "iface_id", "Interfaces"),
        "type_id" : fields.many2one("posix_net.service_type", "Service Type",select=True),
        "enabled" : fields.boolean("Enabled")
    }
    _defaults = {
        "enabled" : True
    }


class posix_net_service_type(osv.Model):
  
    _name="posix_net.service_type"
    _description="Service Type"
    
    _columns = {
        "name" : fields.char("ID", required=True, select=True),
        "port" : fields.integer("Port"),
        "category_ids" : fields.many2many("posix_net.service_category", "posix_net_service_category_rel", "type_id", "category_id", "Category"),
    }
posix_net_service_type()


class posix_net_service_category(osv.Model):
    
    _name="posix_net.service_category"
    _description="Service Category"
    
    _columns = {
        "name" : fields.char("Name", required=True, select=True),
        "parent_id" : fields.many2one("posix_net.service_category", "Parent", select=True)
    }


class posix_net_qos_profile(osv.Model):
  
    _name="posix_net.qos_profile"
    _description="QoS Profile"
    
    _columns = {
        "name" : fields.char("Name", required=True, select=True),
        "priority" : fields.integer("Priority", help="The Priority  -1 (Highest), 0 (Default), 50 (Middle) or 100 (Low), 255 (Very Low)", select=True),    
        "download" : fields.float("Download Kbit/s"),        
        "upload" : fields.float("Upload Kbit/s"),
        "parent_id" : fields.many2one("posix_net.qos_profile", "Parent", select=True),
        "child_ids" : fields.one2many("posix_net.qos_profile","parent_id","Childs")
    }
    _order = "name, id"


class posix_net_firmware(osv.Model):

    _name="posix_net.firmware"
    _description="Firmware"
    
    _columns = {
        "name" : fields.char("Name", required=True, select=True),
        "version" : fields.char("Version", select=True),
        "description" : fields.text("Description"),
        "data" : fields.binary("Data")
    }

class posix_net_vlan(osv.Model):
    
    def copy(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}
        if not default.has_key("vlan_port_ids"):
            default["vlan_port_ids"] = None
            
        res = super(posix_net_vlan, self).copy(cr, uid, oid, default, context)
        return res
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ["name", "vlan"], context=context)
        res = []
        for record in reads:
            name = record["name"]
            if not name:
                name = str(record["vlan"])
            res.append((record["id"], name))
        return res
    
    _name="posix_net.vlan"
    _description="VLAN"
    
    _columns = {
        "unit_id" : fields.many2one("posix_net.unit", "Unit", ondelete="cascade" ),
        "vlan" : fields.integer("VLAN", required=True),
        "device" : fields.char("Device", size=64),
        "name" : fields.char("Name", size=64),
        "vlan_port_ids" : fields.one2many("posix_net.vlan_port", "vlan_id", "VLAN Ports")
    }
    
class posix_net_vlan_port(osv.Model):
    
    def copy(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}
        if not default.has_key("port_id"):
            default["port_id"] = None
        if not default.has_key("vlan_id"):
            default["vlan_id"] = None
            
        res = super(posix_net_vlan_port, self).copy(cr, uid, oid, default, context)
        return res
    
    _name="posix_net.vlan_port"
    _description="VLAN Port"
    _rec_name="port_id"
    
    _columns = {
        "port_id" : fields.many2one("posix_net.port", "Port", required=True),
        "unit_id" : fields.many2one("posix_net.unit", "Unit", ondelete="cascade"),
        "vlan_id" : fields.many2one("posix_net.vlan", "VLAN"),
        "tagged" : fields.boolean("Tagged"),
        "pvid" : fields.boolean("PVID", help="If there is no VLAN given, it will take 0 by default")
    }
    
    