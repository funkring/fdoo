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

from dateutil.relativedelta import relativedelta

from openerp import models, fields, api, _


class UtilReport(models.AbstractModel):
  _name = "util.report"

  def _getReportAttachment(self, report_name, object=None):
    if not object:      
      object = self
      
    attachment_id = self.env["ir.actions.report.xml"]._get_attachment_id(
        self._cr,
        self._uid,
        report_name,
        object,
        context=self._context
    )
    
    if not attachment_id:
      return None
    return self.env["ir.attachment"].browse(attachment_id)
  
  def _renderReport(self, report_name, objects=None, encode=False, 
                    add_pdf_attachments=False, report_title=None):
    
    if not objects:
      objects = self
      
    cr = objects._cr
    uid = objects._uid
    
    report_context = dict(self._context)
    if add_pdf:
      report_context["add_pdf_attachments"]=add_pdf_attachments
    if report_title:
      report_context["report_title"]=report_title
    
    report_obj = self.env.registry["ir.actions.report.xml"]
    report = report_obj._lookup_report(cr, report_name)
    if report:
      values = {}      
      (report_data, report_ext) = report.create(cr, uid, obj.ids, values, context=report_context)
      if len(obj.ids) > 1:
        name_first = obj[0].name_get()[0][1]
        name_last = obj[-1].name_get()[0][1]
        name = "%s-%s.%s" % (util.cleanFileName(name_first), util.cleanFileName(name_last), report_ext)        
      else:
        name_first = obj.name_get()[0][1]
        name = "%s.%s" % (util.cleanFileName(name_first), report_ext)
      if encode:
        report_data = report_data and base64.encodestring(report_data) or None
      return (report_data, report_ext, name)
    return (None, None, None)