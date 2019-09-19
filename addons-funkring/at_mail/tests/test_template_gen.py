# -*- coding: utf-8 -*-
#############################################################################
#
#    Copyright (c) 2018 sunhill technologies GmbH <office@sunhill-technologies.com>
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

from openerp.tests.common import TransactionCase

class TestTemplateGen(TransactionCase):
    """Test template generator"""

    def test_template_gen(self):
      company_obj = self.env["res.company"]
      company = company_obj.browse(company_obj._company_default_get("sunhill.email.task"))
      
      email_template_obj = self.env["email.template"]
      email_template = self.env["email.template"].create({
        "name": "Test Template",
        "model_id": self.env["ir.model"].search([("model","=","res.partner")], limit=1).id,
        "subject": "${object.name}",
        "body_html": "<p>${object.name}</p>"
      })
      
      email_header = self.env["email.template.header"].create({
        "name": "Test Header",
        "partner_id": company.partner_id.id,
        "header_html": "<p>Header for ${object.name}</p>",
        "footer_html": "<p>Footer for ${object.name}</p>"
      })
      
      email_gen_obj = self.env["email.template.gen"]
      email_gen = email_gen_obj.create({
        "name": "Test Generator",
        "header_id": email_header.id,
        "template_id": email_template.id       
      })
      
      email_gen.with_context(lang="de_DE").write({
        "subject": "Test DE ${object.name}",
        "body_html": "<p>Hallo ${object.name}</p>"
      })
      
      email_gen.with_context(lang="en_US").write({
        "subject": "Test ${object.name}",
        "body_html": "<p>Hello ${object.name}</p>"
      })
      
            
      self.assertEqual(email_gen.with_context(lang="en_US").subject,  "Test ${object.name}", "Test subject")
      self.assertEqual(email_gen.with_context(lang="de_DE").subject,  "Test DE ${object.name}", "Test subject DE")
      self.assertEqual(email_gen.with_context(lang="en_US").body_html, "<p>Hello ${object.name}</p>", "Test body")
      self.assertEqual(email_gen.with_context(lang="de_DE").body_html, "<p>Hallo ${object.name}</p>", "Test body DE")
      
      email_header.action_validate()
      self.assertEqual(email_gen.state, "draft", "Check if it is still in draft")
      
      email_gen.action_validate()
      self.assertEqual(email_gen.state, "valid", "Check if valid")
      
      result_en = "<p>Header for %(name)s</p>\n<p>Hello ${object.name}</p>\n<p>Footer for %(name)s</p>" % {
          "name": company.partner_id.name
      }
      result_de = "<p>Header for %(name)s</p>\n<p>Hallo ${object.name}</p>\n<p>Footer for %(name)s</p>" % {
          "name": company.partner_id.name
      }
      
      subject_en = "Test ${object.name}"
      subject_de = "Test DE ${object.name}"
            
      self.assertEqual(email_template.with_context(lang="en_US").body_html, result_en, "Check body EN")
      self.assertEqual(email_template.with_context(lang="de_DE").body_html, result_de, "Check body DE")
      self.assertEqual(email_template.with_context(lang="en_US").subject, subject_en, "Check subject EN")
      self.assertEqual(email_template.with_context(lang="de_DE").subject, subject_de, "Check subject DE")
      
      email_gen2 = email_gen_obj.create({
        "name": "Test Generator",
        "header_id": email_header.id,
        "template_id": email_template.id,
        "body_html": "<p>Hallo2 ${object.name}</p>",
        "subject": "Test2 ${object.name}" 
      })
      
      email_gen2.action_validate()
      self.assertEqual(email_gen.state,"draft", "Check reset to draft state")
      self.assertEqual(email_gen2.state,"valid", "Check valid state")
      
      
      email_gens = email_gen_obj.browse([email_gen.id, email_gen2.id])
      email_gens.write({
        "state": "valid"
      })
      
      email_gens.action_validate()
      self.assertEqual(email_gens[1].state,"draft")
      
      email_header.action_validate()
      self.assertEqual(email_header.state, "valid", "Check valid state of header")
      
      email_header.action_reset()
      email_gen.action_reset()
      
      self.assertEqual(email_header.state, "draft", "Check draft state")
      self.assertEqual(email_gen.state, "draft", "Check draft state")
      
      
      