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

from openerp.osv import fields, osv

class config_rule(osv.Model):
    _name = "posix_net.config.rule"
    _description = "Configuration Rule"
    _columns = {
        "name" : fields.char("Name"),
        "network_id" : fields.many2one("posix_net.network","Network",select=True),
        "priority" : fields.selection([("1","Low"),("5","Normal"),("9","High")],"Priority",select=True),
        "unit_id" : fields.many2one("posix_net.unit","Unit",select=True),
        "iface_id" : fields.many2one("posix_net.iface","Interface",select=True),
        "service_id" : fields.many2one("posix_net.service","Service",select=True),
        "xpath" : fields.char("XPath"),
        "position" : fields.selection([("before","Before"),("after","After"),("inside","Inside"),("replace","Replace"),("attrib","Attribute")],"Position"),
        "sequence" : fields.integer("Sequence"),
        "value" : fields.text("Value")
    }
    _defaults = {
        "sequence" : 10
    }
    _order = 'network_id, unit_id, service_id, iface_id, sequence'

