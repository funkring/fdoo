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

import shutil
import os
import re

OPENWRT_DIR = "~/Work/funkring/openwrt"
OPENWRT_VERSION = "trunk"

TARGETS = ["ar71xx","brcm47xx","brcm24"]
TARGET_LOCK = { "openwrt-brcm-2.4-squashfs" : "brcm24" }
TARGET_DIST_MAP = {"brcm24" : "brcm-2.4"}
TARGET_MAP = {
    "openwrt-ar71xx-generic-ubnt-airrouter-jffs2"   : "openwrt.airrouter",
    "openwrt-ar71xx-generic-ubnt-bullet-jffs2" : "openwrt.bullet",
    "openwrt-ar71xx-generic-ubnt-unifi-jffs2" :  "openwrt.unifi",
    "openwrt-ar71xx-generic-tl-wr741nd-v1-squashfs" : "openwrt.tl.wr741nd1",             
    "openwrt-ar71xx-generic-tl-wr741nd-v2-squashfs" : "openwrt.tl.wr741nd2",
    "openwrt-ar71xx-generic-tl-wr741nd-v4-squashfs" : "openwrt.tl.wr741nd4",
    "openwrt-ar71xx-generic-tl-wr741nd-v4-squashfs" : "openwrt.tl.wr741nd4",
    "openwrt-ar71xx-generic-tl-wr941nd-v2-squashfs" : "openwrt.tl.wr941nd2",
    "openwrt-ar71xx-generic-tl-wr941nd-v3-squashfs" : "openwrt.tl.wr941nd3",
    "openwrt-ar71xx-generic-tl-wr941nd-v4-squashfs" : "openwrt.tl.wr941nd4",
    "openwrt-ar71xx-generic-tl-wr1043nd-v1-jffs2" : "openwrt.tl.wr1043nd1",      
    "openwrt-brcm47xx-squashfs" : "openwrt.wrt54gl",
    "openwrt-brcm-2.4-squashfs" : "openwrt.wrt54gl.brcm24"
}

TARGET_MAP_PATTERN = re.compile("(.*(squashfs|jffs2))(-(factory|sysupgrade))?")
VERSION_PATTERN = re.compile('CONFIG_VERSION_NUMBER="([^"]+)"')

if __name__ == '__main__':
    curdir = os.path.dirname(__file__)
    imagedir = os.path.join(curdir,"image")
    
    for target in TARGETS:
        target_dist = TARGET_DIST_MAP.get(target,target)
        imagedir_source = os.path.expanduser("%s/openwrt-%s-%s/bin/%s" % (OPENWRT_DIR,OPENWRT_VERSION,target,target_dist))        
        if not os.path.exists(imagedir_source):
            imagedir_source = os.path.expanduser("%s/openwrt-%s-%s/bin" % (OPENWRT_DIR,OPENWRT_VERSION,target))
            
        if os.path.exists(imagedir_source):  
            print "found path %s" % (imagedir_source,)
            config_file =  os.path.expanduser("%s/openwrt-%s-%s/.config" % (OPENWRT_DIR,OPENWRT_VERSION,target))
            config = open(config_file,"r").read()
            version = None
            m = VERSION_PATTERN.search(config)
            if m:
                version = m.group(1)                
            else:
                version_file = os.path.expanduser("%s/openwrt-%s-%s/package/base-files/files/etc/openwrt_version" % (OPENWRT_DIR,OPENWRT_VERSION,target))
                if os.path.exists(version_file):
                    version_file_fd = open(version_file)
                    version_str = version_file_fd.read()
                    if len(version_str) and version_str[0]=="v":
                        version=version_str.strip()
            
            if version:
                print "Found Version %s" % (version,)
                for image in os.listdir(imagedir_source):
                    m = TARGET_MAP_PATTERN.search(image)
                    if m:                        
                        image_name = m.group(1)
                        dstimage_name = TARGET_MAP.get(image_name)
                        target_lock = TARGET_LOCK.get(image_name)
                        if not target_lock or target_lock == target:
                            if dstimage_name:                                 
                                image_type = m.group(4)
                                if image_type:
                                    dstimage_name = "%s.%s.%s.bin" % (dstimage_name, version, image_type)
                                else:
                                    dstimage_name = "%s.%s.bin" % (dstimage_name, version)
                                                                                                    
                                dstimage_path = os.path.join(imagedir,dstimage_name)
                                srcimage_path = os.path.join(imagedir_source,image)
                                print "Copy image from %s to %s" % (srcimage_path, dstimage_path)
                                shutil.copy(srcimage_path, dstimage_path)
            else:    
                print "No version found for %s" % (imagedir_source,)
            
                
    
    pass