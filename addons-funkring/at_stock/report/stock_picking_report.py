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

import time
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.addons.at_base import util

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)

        self.localcontext.update({
            "get_state" : self._get_state,
        })


    def _get_state(self, picking):
        state = ""
        if picking.state == "draft":
            state = _("Draft")
        elif picking.state == "cancel":
            state = _("Cancelled")
        elif picking.state == "waiting":
            state = _("Waiting Another Operation")
        elif picking.state == "confirmed":
            state = _("Waiting Availability")
        elif picking.state == "partially_available":
            state = _("Partially Available")
        elif picking.state == "assigned":
            state = _("Ready to Transfer")
        elif picking.state == "done":
            state = _("Done")

        return state





