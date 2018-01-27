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
      self.localcontext["company_cur"]=""
      
      company_id = self.pool.get("res.users")._get_company(self.cr, self.uid, context=context)
      if company_id:
        
        company = self.pool.get("res.company").browse(self.cr, self.uid, company_id, context=context)
        if company:
        
            self.localcontext["company"]=company
            if company:
              
                # basic
                self.localcontext["company_name"]=company.name
                
                # currency
                currency = company.currency_id
                self.localcontext["company_cur"] = currency.symbol
                
                # address
                partner = company.partner_id
                self.localcontext["company_phone"]=partner.phone or ""
                self.localcontext["company_fax"]=partner.fax or ""
                self.localcontext["company_email"]=partner.email or ""
  
  
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
