# -*- coding: utf-8 -*-
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

from openerp.osv import osv

class prov_openwrt(osv.AbstractModel):
    
    def _build(self, cr, uid, builder, context=None):
        super(prov_openwrt,self)._build(cr, uid, builder, context=context)
       
        builder.addConfigFile("/etc/config/system", "text/openwrt-config", 
         [("system",[
                ("hostname", builder.unit.name)
                ("zonename", "Europe/Vienna"),
                ("timezone", "CET-1CEST,M3.5.0,M10.5.0/3")]),
          
          ("timeserver",[
                  ("server",["0.openwrt.pool.ntp.org",
                             "1.openwrt.pool.ntp.org",
                             "2.openwrt.pool.ntp.org",
                             "3.openwrt.pool.ntp.org"])           
           ])        
         ])
        
        
        
        
        
    
    _name = "prov.openwrt"
    _description = "OpenWRT Provisioning"
    _inherit = ["prov.router.wlan"]
    
    