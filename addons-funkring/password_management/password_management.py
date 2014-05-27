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

from openerp.osv import fields,osv

class password_entry(osv.osv):
    _rec_name = "subject" 
    _columns = {
        "subject" : fields.char("Name",select=True),
        "login" : fields.char("Login",select=True),
        "password" : fields.char("Password",select=True),
        "partner_id" : fields.many2one("res.partner","Partner", select=True, ondelete="cascade") ,
        "group_id" : fields.many2one("res.groups","Group"),
        "description" : fields.text("Description", select=True),
        "company_id" : fields.related("partner_id","company_id",type="many2one",relation="res.company",string="Company",store=True,readonly=True,select=True)
    }    
    _name="password.entry"
    _description="Password Entry"


class res_partner(osv.osv):
    _columns = {
        "password_ids" : fields.one2many("password.entry","partner_id","Passwords")
    }    
    _inherit = "res.partner"
