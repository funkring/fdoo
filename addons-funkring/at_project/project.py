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

class project_division(osv.Model):
    _name = "project.task.division"
    _description = "Task Division"
    _columns =  {
        "name" : fields.char("Name",translate=True),
        "sequence" : fields.integer("Sequence"),
        "fold" : fields.boolean("Folded in Kanban View",
                                help="Is this division folded in kanban view when der are no records in division")
    }
    _order = "sequence"
    _defaults = {
        "sequence" : 10
    }


class project_task(osv.Model):
    
    def _read_group_division_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        division_obj = self.pool.get('project.task.division')
        order = division_obj._order
        access_rights_uid = access_rights_uid or uid
        if read_group_order == 'division_id desc':
            order = '%s desc' % order
        search_domain = []
        division_ids = division_obj._search(cr, uid, search_domain, order=order, access_rights_uid=access_rights_uid, context=context)
        result = division_obj.name_get(cr, access_rights_uid, division_ids, context=context)
        # restore order of the search
        result.sort(lambda x,y: cmp(division_ids.index(x[0]), division_ids.index(y[0])))

        fold = {}
        for division in division_obj.browse(cr, access_rights_uid, division_ids, context=context):
            fold[division.id] = division.fold
        return result, fold
    
    
    _inherit = "project.task"
    _columns = {
        "division_id" : fields.many2one("project.task.division","Division",select=True)
    }
    _group_by_full = {
        "division_id" : _read_group_division_ids
    }