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

{
    "name" : "oerp.at Network",
    "description":"""
oerp.at Network module
=========================================

 * Complete organisation of networks
 * Automatic configuration of devices
""",
    "version" : "1.2",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Network",
    "depends" : ["at_base","posix","posix_log","dataset", "password_management"],#, "at_pos"],
    "data" :   ["security.xml",
                "menu.xml",
                "precision.xml",
                "view/vlan_view.xml",
                "view/wlan_frequency_view.xml",                    
                "view/network_view.xml", 
                "view/unit_view.xml",
                "view/unit_type_view.xml",
                "view/unit_category_view.xml",                    
                "view/port_category_view.xml",
                "view/port_type_view.xml",
                "view/port_view.xml",
                "view/ipv4_view.xml",
                "view/ipv6_view.xml",
                "view/frequency_mapping_view.xml",
                "view/frequency_mapping_channel_wizard.xml",
                #"view/ipv4_wizard.xml",
                #"view/ipv6_wizard.xml",
                "view/qos_profile_view.xml",
                "view/firmware_view.xml",
                "view/service_view.xml",
                "view/service_type_view.xml",
                "view/service_category_view.xml",
                "view/iface_view.xml",                
                "view/log_view.xml",
                "wizard/connection_wizard.xml",
                "report/network_report.xml",
                "data/unit_type.xml",
                #"data/data_view.xml"
                ],
    "auto_install": False,
    "installable": True
}
