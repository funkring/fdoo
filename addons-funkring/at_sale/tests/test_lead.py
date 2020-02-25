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

import base64

from openerp.tests.common import TransactionCase

class TestLead(TransactionCase):
  """Test lead"""
  
  def test_lead_data_move(self):
    shop = self.env["sale.shop"].search([], limit=1)
    lead_obj = self.env["crm.lead"]
    lead = lead_obj.create({
      "name": "Test Lead"
    })
    
    # add post    
    post_id = lead.message_post("Test 1234")
    
    # add attachment
    attachment_obj = self.env["ir.attachment"]
    att = attachment_obj.create({
      "name": "Test.txt",
      "datas": base64.encodestring("Testfile Data"),
      "datas_fname": "Test.txt",
      "res_model": lead._model._name,
      "res_id": lead.id
    })
      
    # create order
    order = lead._create_order({
      "shop_id": shop.id,
      "partner_id": 1
    })  
    
    # move history
    lead._move_history(order)
    
    # check attachment movement
    self.assertEqual(att.res_model, "sale.order", "check model")
    self.assertEqual(att.res_id, order.id, "check id")
    
    # check messages
    messages = order.message_ids
    self.assertEqual(len(messages), 4, "check messages")
    
    found = 0
    for message in messages:
      if message.body.find("Test 1234") >= 0:
        found+=1

    self.assertEqual(found, 1, "check if message moved")    
    