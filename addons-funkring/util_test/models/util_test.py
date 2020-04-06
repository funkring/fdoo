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

import os
import base64
import logging

from openerp import models
from openerp import tools

_logger = logging.getLogger(__name__)

class UtilTest(models.AbstractModel):
    _name = "util.test"
    
    def _testDownloadAttachments(self, obj=None, prefix=None):
        if not obj:
            obj = self
        
        test_download = tools.config.get("test_download")
        res = []
        if test_download:
            att_obj = obj.env["ir.attachment"]
            for att in att_obj.search(
                [("res_model", "=", obj._model._name), ("res_id", "=", obj.id)]
            ):
                file_name = att.datas_fname
                if prefix:
                    file_name = "%s%s" % (prefix, file_name)
                    
                download_path = os.path.join(test_download, att.datas_fname)
                with open(download_path, "wb") as f:
                    if att.datas:
                        f.write(base64.decodestring(att.datas))
                
                res.append(download_path)
                _logger.info("Download %s" % download_path)
                
        return res
