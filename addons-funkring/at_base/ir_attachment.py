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
from openerp.tools.translate import _
from werkzeug.datastructures import FileStorage

import base64
import os
import uuid

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import logging
_logger = logging.getLogger(__name__)

class ir_attachment(osv.Model):
   
    def _file_write(self, cr, uid, value):
        """ extend file write to support streams """
        
        # check if it is a string
        if isinstance(value, basestring):
            return super(ir_attachment,self)._file_write(cr, uid, value)
        
        # create temp file
        full_temp = self._full_path(cr, uid, "tmp_%s" % uuid.uuid4())
        fname = None
        try:
            # save stream as temp file
            if isinstance(value, FileStorage):
                value.save(full_temp)
            else:
                with open(file_path,"wb") as f:
                    for chunk in iter(lambda: value.read(16384), b""):
                        f.write(chunk)
                        
            # check for rename, and create path
            # if the same file exist, take the existing file
            fname, full_path = self._get_path(cr, uid, None, file_path=full_temp)
            if not os.path.isfile(full_path) and full_path != full_temp:
                os.rename(full_temp, full_path)                
                      
        finally:
            # remove temp file
            if os.path.isfile(full_temp):
                try:
                    os.unlink(full_temp)
                except Exception as e:
                    _logger.exception("unable to unlink temp file %s" % full_temp, e)
        
        return fname
    
    def _file_open(self, cr, uid, attachment, context=None):
        location = self._storage(cr, uid, context)
        if location == "db":
            return None
        if not attachment.store_fname:
            return None
        
        file_path = self._full_path(cr, uid, attachment.store_fname)
        if not os.path.isfile(file_path):
            return None
        return open(file_path,"rb")
        
    def _save_file(self, cr, uid, oid, values, context=None):
        assert values

        store_fname = values["store_fname"]
        location = self._storage(cr, uid, context)
        full_path = self._full_path(cr, uid, store_fname)
        file_size = os.path.getsize(full_path)    
        
        # check store_fname for delete
        fname_to_delete = None
        
        # open file        
        if location == "db":
            with open(full_path) as fp:
                buf = StringIO()
                base64.encode(fp, buf)
                
                next_values = {"db_datas":buf.getvalue()}
                next_values.update(values)
                next_values.pop("store_fname")
                values = next_values

        # update file                
        if oid:    
            fname_to_delete = self.read(cr, uid, oid, ["store_fname"], context=context)["store_fname"]
            self.write(cr, uid, oid, values, context=context)
        # write new file
        else:
            oid = self.create(cr, uid, values, context=context)
                
        # After de-referencing the file in the database, check whether we need
        # to garbage-collect it on the filesystem
        if fname_to_delete:
            self._file_delete(cr, uid, fname_to_delete)
        
        # update file size
        # have to be called additional, because on default file was written in function field
        # ... and for security reasons, odoo developer remove the file attribute in the values
        cr.execute("UPDATE ir_attachment SET file_size=%s WHERE id=%s", (file_size, oid))
        return oid
            
    
    _name = "ir.attachment"
    _inherit = "ir.attachment"
    _columns = {
        "origin" : fields.char("Origin")
    }    
    