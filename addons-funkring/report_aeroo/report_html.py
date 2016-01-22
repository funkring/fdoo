# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp import api, models
from genshi.filters import HTMLSanitizer
from genshi.input import HTML
import StringIO

class report_html(models.AbstractModel):
    _name = "report.html"
    _description = "Html Report"
    
    @api.multi
    def render_html(self, data=None):
        if data:
            html = data.get("html") or None
            if html:
                html = HTML(html,"UTF-8")
                sanitize = HTMLSanitizer()
                return StringIO.StringIO(html | sanitize).getvalue()
        return None