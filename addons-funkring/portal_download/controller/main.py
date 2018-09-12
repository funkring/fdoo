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
from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.web.controllers.main import content_disposition
from openerp.tools.translate import _

import logging
import mimetypes

_logger = logging.getLogger(__name__)

class portal_download_ctrl(http.Controller):
    
    @http.route(["/portal_download/start/<int:download_id>"], type="http", auth="public", methods=["GET"])
    def download_start(self, download_id=None, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        
        if isinstance(download_id, basestring):
            download_id = int(download_id)

        # check for download key           
        perm_obj = request.registry["portal.download.perm"]
        user_obj = request.registry["res.users"]
        perm_ids = None
        download_key = kwargs.get("key")        
        if download_key:
            perm_ids = perm_obj.search(cr, SUPERUSER_ID, [("download_key_intern","=",download_key)])
            if perm_ids:
                perm = perm_obj.browse(cr, SUPERUSER_ID, perm_ids[0])
                uid = user_obj.search_id(cr, SUPERUSER_ID, [("partner_id","=",perm.partner_id.id)])
                if not uid:
                    return request.not_found()
        
        try:
          download_obj = request.registry["portal.download"]                
          download = download_obj.browse(cr, uid, download_id, context=context)
          if not download or not download.active:
              return request.not_found()
        except:
          return request.not_found()
        
        att_obj = request.registry["ir.attachment"]
        att_ids = att_obj.search(cr, uid, [("res_model","=","portal.download"),("res_id","=",download.id)], limit=1)
        if not att_ids:
            return request.not_found()
        
        att = att_obj.browse(cr, SUPERUSER_ID, att_ids[0], context=context)
        att_mimetype = mimetypes.guess_type(att.datas_fname or "")[0] or "application/octet-stream"
        att_disp = content_disposition(att.datas_fname)
        
        file_out = None
        if att.store_fname:
            full_path = att_obj._full_path(cr, uid, att.store_fname)
            try:
                file_out = open(full_path,'rb')
            except IOError:
                _logger.exception("Unable to load file %s", full_path)
                return request.not_found()
                      
        else:
            return request.not_found()
        
                
        if not perm_ids:           
            user = user_obj.browse(cr, SUPERUSER_ID, uid, context=context)
            perm_ids = perm_obj.search(cr, SUPERUSER_ID, [("partner_id","=",user.partner_id.id),("download_id","=",download_id)])
            
        if perm_ids:
            for perm_id in perm_ids:
                download_count = perm_obj.read(cr, SUPERUSER_ID, perm_id, ["download_count"], context=context)["download_count"]
                perm_obj.write(cr, SUPERUSER_ID, perm_id, {"download_count":download_count+1}, context=context)
                
        return request.make_response(
                file_out,
                [("Content-Type", att_mimetype),
                 ("Content-Disposition",att_disp)])
