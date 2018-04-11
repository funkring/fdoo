# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import SUPERUSER_ID

from openerp.addons.web import http
from openerp.addons.web.http import request


import json
from werkzeug.exceptions import BadRequest

class task_log(http.Controller):

    @http.route(["/http/log/<int:task_id>/<secret>"], type="http", auth="public", methods=['POST'])
    def log(self, task_id=None, secret=None, progress=None, **kwargs):      
      cr, uid, context = request.cr, request.uid, request.context

      scecret_ids = request.registry["automation.task.secret"].search(cr, SUPERUSER_ID, [("task_id","=", task_id),("secret","=",secret)])      
      if scecret_ids:
        payload = kwargs
        payload["task_id"] = task_id
        try:
          # check if progress passed
          # .. modify progress
          if progress:
            try:
              progress = float(progress)
              request.registry["automation.task.stage"].write(cr, SUPERUSER_ID,
                      long(payload["stage_id"]), {"progress": progress}, context=context)
            except ValueError:
              pass           
            
          # log
          res = request.registry["automation.task.log"].create(cr, SUPERUSER_ID, payload, context=context)
          cr.commit()
          return str(res)
        finally:
          cr.rollback()
      
      return BadRequest()
    
    @http.route(["/http/stage/<int:task_id>/<secret>"], type="http", auth="public", methods=['POST'])
    def stage(self, task_id=None, secret=None, **kwargs):      
      cr, uid, context = request.cr, request.uid, request.context
      scecret_ids = request.registry["automation.task.secret"].search(cr, SUPERUSER_ID, [("task_id","=", task_id),("secret","=",secret)])      
      if scecret_ids:
        payload = kwargs
        payload["task_id"] = task_id
        try:
          # create stage
          res = request.registry["automation.task.stage"].create(cr, SUPERUSER_ID, payload, context=context)
          cr.commit()
          return str(res)
        finally:
          cr.rollback()

      return BadRequest()
    
    
    @http.route(["/http/progress/<int:task_id>/<secret>"], type="http", auth="public", methods=['POST'])
    def progress(self, task_id=None, secret=None, stage_id=None, **kwargs):      
      cr, uid, context = request.cr, request.uid, request.context
      
      if isinstance(stage_id,basestring):
        stage_id = long(stage_id)
                
      scecret_ids = request.registry["automation.task.secret"].search(cr, SUPERUSER_ID, [("task_id","=", task_id),("secret","=",secret)])      
      if scecret_ids:
        payload = kwargs
        payload["task_id"] = task_id
        try:          
          stage_obj = request.registry["automation.task.stage"]
          res = request.registry["automation.task.stage"].write(cr, SUPERUSER_ID, [stage_id], payload, context=context)
          cr.commit()
          return str(res)
        finally:
          cr.rollback()
      
      return BadRequest()

  