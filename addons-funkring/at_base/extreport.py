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

from openerp.report import report_sxw

import qrcode
import qrcode.image.svg
from qrcode import constants 

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


class basic_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
      super(basic_parser, self).__init__(cr, uid, name, context=context)
      self.localcontext["get_qrimage"] = self.get_qrimage
      self.localcontext["company_name"]=""
      self.localcontext["company_phone"]=""
      self.localcontext["company_fax"]=""
      self.localcontext["company_email"]=""
      user = self.localcontext.get("user")
      if user:
          company = user.company_id
          self.localcontext["company"]=company
          if company:
              self.localcontext["company_name"]=company.name
              address_rec = company.partner_id and company.partner_id
              if address_rec:
                  self.localcontext["company_phone"]=address_rec.phone
                  self.localcontext["company_fax"]=address_rec.fax
                  self.localcontext["company_email"]=address_rec.email
                    
    def get_qrimage(self, data):
      if not data:
        return None
      
      qr = qrcode.QRCode(
              box_size=2.0,
              border=4
           )
      
      qr.add_data(data, optimize=0)
      qr.make()
      im = qr.make_image()
      image_data = StringIO.StringIO()
      im.save(image_data,"PNG")
      return image_data.getvalue().encode("base64")
