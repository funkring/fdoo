##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from openerp.osv import osv,fields
from DocumentConverter import DocumentConverter

class OpenOffice_service (DocumentConverter):
    def __init__(self, cr, host=None, port=None):
        if host is None and port is None:
            cr.execute("SELECT host, port FROM oo_config")
            host, port = cr.fetchone()
        DocumentConverter.__init__(self, host, port)

class oo_config(osv.osv):
    '''
        OpenOffice connection
    '''
    _name = 'oo.config'
    _description = 'OpenOffice connection'

    _columns = {
        'host':fields.char('Host', size=128, required=True),
        'port': fields.integer('Port', required=True),
    }
    
    def _lookup_service(self, cr, uid, context=None):
        return OpenOffice_service(cr)

oo_config()

class report_xml(osv.osv):
    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'

    _columns = {
        'process_sep':fields.boolean('Process separately'),
        
    }

report_xml()

