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

from openerp.osv import fields, osv

class commission_recalc_wizard(osv.osv_memory):
    
    def do_recalc(self, cr, uid, ids, context=None):
        return { "type" : "ir.actions.act_window_close" }
    
    _name = "commission.recalc_wizard"
    _description = "Wizard to recalculate the commissions"
    _columns = {
        "date_from" : fields.date("Date from", help="The date which you entered is involved!"),
        "date_to" : fields.date("Date to", help="The date which you entered is involved!")
    }
    
