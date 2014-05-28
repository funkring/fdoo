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

from openerp.report import interface
from openerp.osv import osv
import tempfile
import tarfile
import shutil
import openerp.pooler
import os
from openerp.tools.translate import _
from openerp.addons.at_base import util
import openerp.tools
import re
import ipcalc
from olsr_support import olsr_support
from vtun_support import vtun_support


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

PROV_CREATOR_DICT = {}

IMAGE_PATTERN = re.compile("((\\.?[0-9a-z])+)\\.v([0-9]+([.\\-_][0-9a-z]+)+[0-9])", re.I)
def parse_image_name(image):
    m = IMAGE_PATTERN.search(image)    
    return m and (m.group(1),m.group(3)) or None

def iface_ipv4_get(iface):
    if iface and iface.ipv4_ip and iface.ipv4_mask:
        return ipcalc.Network(iface.ipv4_ip,iface.ipv4_mask,version=4)
    return None

def net_ipv4_get(network):    
    if network:
        address = network.ipv4_address_id
        if address:
            return ipcalc.Network(address.ip,address.mask,version=4)
    return None

class prov_creator(olsr_support,vtun_support):
    def __init__(self):
        self.cr=None
        self.uid=None
        self.pool=None
        self.build_dir=None
        self.unit=None
        self.localcontext=None
        self.properties=None
        self.name=None
        self.hostname=None
        self.admin=None
        self.image_dir=None
        
    def build_image(self):
        return None    
        
    def prepare(self):
        return True
    
    def default_user(self):
        return "root"
    
    def default_password(self):
        return "funkring"     
    
    def image_builder_name(self):
        return None
    
    def image_builder_profile(self):
        return None    
    
    def image_builder_packages(self):
        return None
 
    def use_bridge_name_as_iface(self):
        return True
        
    def create(self):
        pass


class report_prov(interface.report_int):
    def __init__(self,name):
        super(report_prov,self).__init__(name)
         
    def _add_ifaces(self,filtered_ifaces,ifaces,when_private=False,when_public=False,when_protected=False):
        for iface in ifaces:
            network = iface.network_id
            network_parent = network.parent_id or None                                        
            if not network_parent and when_private or (when_private and network_parent.private):
                filtered_ifaces.append(iface)
            elif network_parent:
                if when_protected and network_parent.protected:
                    filtered_ifaces.append(iface)
                elif when_public and network_parent.public:
                    filtered_ifaces.append(iface)
               
    def create(self, cr, uid, ids, datas, context=None):
        pool = pooler.get_pool(cr.dbname)
        model = datas.get("model")
        
        #get image files
        image_dir = tools.get_path("posix_net/prov/image")        
        image_files = {}
        if os.path.exists(image_dir):
            for image in os.listdir(image_dir):
                t = parse_image_name(image)
                if t:                    
                    device = t[0].lower()
                    images = image_files.get(device)
                    if not images:
                        images = []
                        image_files[device]=images                    
                    images.append(image)                    
                                    
        #sort image files
        for files in image_files.values():
            files.sort()
        
        #get model
        if ids and model and model == "posix_net.unit":
            unit_obj = pool.get(model)                
            temp_dir = tempfile.mkdtemp("_funet-prov")
            unit_pos = 0
            if temp_dir:                        
                try:                    
                    image_temp_dir = os.path.join(temp_dir,"image")
                    os.makedirs(image_temp_dir)                
                
                    tar_buf = StringIO()
                    tar = tarfile.open(fileobj=tar_buf,mode="w")
                    
                    used_drivers=set()
                    used_images=set()
                    notexisting_drivers=set()
                    
                    for unit in unit_obj.browse(cr,uid,ids,context):
                        unit_type = unit.type_id
                        if unit_type.code:                    
                            driverparts = []
                            driver = None
                            for t in unit_type.code.split("."):
                                driverparts.append(t)
                                drivername = "_".join(driverparts)
                                if drivername in used_drivers:
                                    driver = drivername                                
                                elif not drivername in notexisting_drivers:
                                    try:
                                        exec "import %s" % (drivername,)
                                        driver = drivername
                                    except:
                                        notexisting_drivers.add(drivername)
                                else:
                                    break
                        
                            if not driver:
                                raise osv.except_osv(_("Error !"), _("Driver %s not found") % (unit_type.code,))
                                    
                            creator = eval("%s.creator()" % (driver,))                                                
                            if creator:
                                #add driver
                                used_drivers.add(driver)
                                
                                #properties
                                properties = {}
                                properties["name"]=unit.name  
                                properties["user"]=unit.user
                                properties["password"]=unit.password                              
                                # alternative user data
                                if unit.last_user:
                                    properties["last_user"]=unit.last_user
                                if unit.last_password:
                                    properties["last_password"]=unit.last_password
                                # save image builder
                                image_builder_name = creator.image_builder_name()
                                image_builder_profile = creator.image_builder_profile()
                                if image_builder_name and image_builder_profile:
                                    properties["image_builder_name"]=image_builder_name
                                    properties["image_builder_profile"]=image_builder_profile
                                    image_builder_packages = creator.image_builder_packages()
                                    if image_builder_packages:
                                        properties["image_builder_packages"]=" ".join(image_builder_packages)
                                #
                                #create create directory
                                unit_dir = "%s-%s" % (str(unit_pos).rjust(5,"0"),unit_type.code)
                                unit_temp_dir = os.path.join(temp_dir,unit_dir)
                                
                                #start creator
                                creator.name=unit_type.code
                                creator.cr=cr
                                creator.uid=uid
                                creator.pool=pool
                                creator.build_dir=unit_temp_dir
                                creator.unit=unit
                                creator.localcontext=context
                                creator.properties=properties
                                creator.hostname = "%s.funet.at" % (unit.name,)
                                                                
                                if creator.prepare():
                                    os.makedirs(unit_temp_dir)                                
                                    creator.create()
                                    ip_ifaces = []                                                        
                                    self._add_ifaces(ip_ifaces,unit.iface_ids,when_protected=True)     
                                    self._add_ifaces(ip_ifaces,unit.iface_ids,when_public=True)
                                    self._add_ifaces(ip_ifaces,unit.iface_ids,when_private=True)
                                    #                                    
                                    counter_ipv4 = 0
                                    counter_ipv6 = 0
                                    for iface in ip_ifaces:
                                        network = iface.network_id
                                        if network.ipv4:
                                            properties["ipv4.%s" % (counter_ipv4,)]=network.ipv4_address_id.ip
                                            counter_ipv4+=1
                                        if network.ipv6:
                                            properties["ipv6.%s" % (counter_ipv6,)]=network.ipv6_address_id.ip
                                            counter_ipv6+=1
                                    # add alternative ip4
                                    if unit.last_ipv4:
                                        properties["ipv4.%s" % (counter_ipv4,)]=unit.last_ipv4
                                        counter_ipv4+=1
                                    # add alternative ip6
                                    if unit.last_ipv6:
                                        properties["ipv6.%s" % (counter_ipv6,)]=unit.last_ipv6
                                        counter_ipv6+=1      
                                
                                    #check if image was created on the fly
                                    build_image = creator.build_image()
                                    if build_image:
                                        image_temp_file = os.path.join(image_temp_dir,build_image[0])
                                        image_src_file = os.path.join(build_image[1])
                                        shutil.copyfile(image_src_file, image_temp_file)
                                        properties["image.0"]="image/%s" % (build_image[0],)
                                    #if static image                                    
                                    else: 
                                        #search image
                                        imageparts = []
                                        images = None
                                        used_image = None
                                        for t in unit_type.code.split("."):
                                            imageparts.append(t)
                                            image_search = ".".join(imageparts)
                                            found_images = image_files.get(image_search)
                                            if not found_images and images:
                                                break                                    
                                            images = found_images
                                            used_image = image_search
                                        
                                        #set images                                
                                        if images:                                 
                                            i=0   
                                            used_images.add(used_image)         
                                            for image in images:
                                                properties[("image.%s") % (i,)]="image/%s" % (image,)
                                                i+=1
                                        
                                    #write properties file
                                    util.writeProperties(os.path.join(unit_temp_dir,"device.info"),properties)
                                
                    if used_images:                       
                        for used_image in used_images:
                            images = image_files.get(used_image)
                            for image in images:
                                image_temp_file = os.path.join(image_temp_dir,image)
                                image_src_file = os.path.join(image_dir,image)
                                shutil.copyfile(image_src_file, image_temp_file)
                                                                                       
                    #add temp directory to tar file
                    tar.add(temp_dir,arcname="funet-prov")
                    tar.close()                    
                    return tar_buf.getvalue(),"funet-prov"
                finally:
                    shutil.rmtree(temp_dir)
        
        raise osv.except_osv(_('Error !'), _('Unable to create provisioning file'))          
        
        
report_prov("report.posix_net.provisioning")
