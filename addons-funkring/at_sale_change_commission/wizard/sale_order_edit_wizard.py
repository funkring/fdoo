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
from openerp.exceptions import Warning

class sale_order_edit_wizard_line(models.TransientModel):
    _inherit = "sale.order.edit.wizard.line"
    
    commission_custom = fields.Float("Custom Commission %")
    

class sale_order_edit_wizard(models.TransientModel):
    _inherit = "sale.order.edit.wizard"
    
    recalc_commission = fields.Boolean("Recalc Commission")
    
    @api.model
    def _get_line_default(self, line):
      res = super(sale_order_edit_wizard, self)._get_line_default(line)
      res["commission_custom"] = line.commission_custom
      return res
      
    def _prepare_line_modification(self, line_modify):
      res = super(sale_order_edit_wizard, self)._prepare_line_modification(line_modify)
      res["commission_custom"] = line_modify.commission_custom
      return res
    
    @api.one
    def _after_modified(self):
      super(sale_order_edit_wizard, self)._after_modified()
      # recalc commission
      if self.recalc_commission:
        self.order_id._calc_sale_commission(force=True)
