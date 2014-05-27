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

class project_task(osv.osv):
    _inherit = "project.task"
    _columns = {
        "checkpoint_ids" : fields.one2many("project.task_checklist","task_id","Checkpoints"),
    }

class project_task_checklist(osv.osv):
        
    _name = "project.task_checklist"
    _description = "Checklist"    
    _columns = {
            
        "name" : fields.char("Name", size=128),
        "task_id" : fields.many2one("project.task","Project Task"),       
        "check" : fields.boolean("Check"),
        "sequence" : fields.integer("Sequence")
    }
    _defaults = {
        "sequence" : 10
    }
    _order = "sequence asc"
