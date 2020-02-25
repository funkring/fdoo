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
from openerp.addons.at_base import util, helper

class crm_lead(models.Model):
  _inherit = "crm.lead"
  
  def _move_attachments(self, obj):
    ids = self.ids
    if ids:   
      attachments = self.env["ir.attachment"].search([
          ("res_model","=","crm.lead"),
          ("res_id","in",ids)])
      
      attachments.write({
        "res_id": obj.id,
        "res_model": obj._model._name
      })
  
  def _move_messages(self, obj):
    for lead in self:
      for message in lead.message_ids:
        message.write({
          "model": obj._model._name,
          "res_id": obj.id
        })

  def _move_history(self, obj):
    self._move_messages(obj)
    self._move_attachments(obj)
    
  def _create_order(self, values=None):
    if values is None:
      values = {}
    else:
      values = values.copy()
      
    order_obj = self.env["sale.order"]
    
    shop_id = values.get("shop_id")
    if shop_id:
      helper.onChangeValuesEnv(order_obj, values, 
                               order_obj.onchange_shop_id(shop_id, "draft", None)) 
    
    partner_id = values.get("partner_id")
    if partner_id:
      helper.onChangeValuesEnv(order_obj, values, 
                               order_obj.onchange_partner_id(partner_id,
                                                              shop_id=values.get("shop_id"))) 
    return order_obj.create(values)
