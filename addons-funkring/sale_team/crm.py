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

from openerp.osv import fields,osv

class crm_case_section(osv.osv):
    
    def _members_text(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for section in self.browse(cr, uid, ids, context):
            members = [m.name for m in section.member_ids]
            res[section.id]=", ".join(members)                            
        return res
    
    _inherit = "crm.case.section"
    _columns = {
        "members_text" : fields.function(_members_text, type="text", string="Members", store=False)
    }
crm_case_section()