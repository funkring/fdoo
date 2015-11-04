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

from openerp import http
from openerp.http import request
from openerp.addons.web.controllers.main import serialize_exception
from openerp.addons.web.controllers.main import Binary
from openerp.addons.web.controllers.main import content_disposition
import simplejson

import logging
_logger = logging.getLogger(__name__)

class BinaryExtension(Binary):

    @http.route()
    def saveas(self, model, field, id=None, filename_field=None, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        if id and model == "ir.attachment" and field=="datas":
            att_obj = request.registry['ir.attachment']
            att = att_obj.browse(cr, uid, int(id), context=context)
            fp = att_obj._file_open(cr, uid, att, context=context)
            if fp:
                return request.make_response(fp,
                    [('Content-Type', 'application/octet-stream'),
                     ('Content-Length',str(att.file_size)),
                     ('Content-Disposition', content_disposition(att.datas_fname))])

        return super(BinaryExtension, self).saveas(model, field, id=id, filename_field=filename_field, **kw)
       
    @http.route()
    def upload_attachment(self, callback, model, id, ufile):
        att_obj = request.registry['ir.attachment']
        out = """<script language="javascript" type="text/javascript">
                    var win = window.top.window;
                    win.jQuery(win).trigger(%s, %s);
                </script>"""
        
        store_fname = None
        try:
            # write temp            
            store_fname = att_obj._file_write(request.cr, request.uid, ufile)            
            values = {
                "name": ufile.filename,
                "datas_fname": ufile.filename,
                "res_model": model,
                "res_id": int(id),
                "store_fname" : store_fname
            }
            
            # save file
            attachment_id = att_obj._save_file(request.cr, request.uid, None, values, request.context)
            
            # return args 
            args = {
                'filename': ufile.filename,
                'id':  attachment_id
            }
            
        except Exception:
            
            # delete file on exception
            if store_fname:
                att_obj._file_delete(request.cr, request.uid, store_fname)
                
            args = {'error': "Something horrible happened"}
            _logger.exception("Fail to upload attachment %s" % ufile.filename)
            
        return out % (simplejson.dumps(callback), simplejson.dumps(args))