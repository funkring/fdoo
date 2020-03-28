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

from openerp import models, fields, api, _

class bmd_reconcil_profile(models.Model):
    _name = "bmd.reconcil.profile"
    _description = "BMD Reconciliation Profile"
        
    name = fields.Char("Name", required=True)
    company_id = fields.Many2one("res.company", "Company", required=True, 
         default=lambda self: self.env['res.company']._company_default_get('bmd.reconcil.profile'))
    
    journal_id = fields.Many2one("account.journal" "Journal", required=True)
    exclude = fields.Char("Exclude Flag")
    

class bmd_reconcil(models.Model):
    _name = "bmd.reconcil"
    _description = "BMD Reconciliation"
    
    name = fields.Char("Name", required=True)
    profile_id = fields.Many2one("bmd.reconcil.profile", "Profile", required=True)
    