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

import urllib
from openerp.osv import osv
from document_ftp import ftpserver

class ir_attachment(osv.osv):
    
    def external_res_url(self, cr, uid,  res_model, res_id, context=None):
        res = super(ir_attachment,self).folder_link(cr,uid,res_model, res_id, context=context)
        if not res:
            dir_obj = self.pool.get("document.directory")
            folder_ids = dir_obj.search(cr,uid,[("type","=","ressource"),("ressource_type_id","!=",False),
                                   ("ressource_type_id.model","=",res_model),"|",("domain","=",False),("domain","=","[]")])
            
            if folder_ids:
                folder = dir_obj.browse(cr,uid,folder_ids[0],context=context)
                if folder.resource_field:
                    res_obj = self.pool.get(res_model)                    
                    res_dir = res_obj.read(cr,uid,res_id,[folder.resource_field.name],context)[folder.resource_field.name]
                    if res_dir:
                        user_pool = self.pool.get("res.users")
                        current_user = user_pool.browse(cr, uid, uid, context=context)
                        data_pool = self.pool.get("ir.model.data")
                        aid = data_pool._get_id(cr, uid, "document_ftp", "action_document_browse")
                        aid = data_pool.browse(cr, uid, aid, context=context).res_id
                        ftp_url = self.pool.get("ir.actions.url").browse(cr, uid, aid, context=context)
                        res = ftp_url.url and ftp_url.url.split("ftp://") or []
                        if res:
                            res = res[1]
                            if res[-1] == "/":
                                res = res[:-1]
                        else:
                            res = "%s:%s" %(ftpserver.HOST, ftpserver.PORT)            
                        res = "ftp://%s:%s@%s/%s/%s"%(current_user.login, urllib.quote(current_user.password), res, urllib.quote(folder.name), urllib.quote(res_dir) )
            
        return res
    
    _inherit = "ir.attachment"
ir_attachment()
