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

from openerp import models, fields, api, _


class email_template_header(models.Model):
    _name = "email.template.header"
    _description = "E-Mail Template Header"

    name = fields.Char("Name", required=True)
    partner_id = fields.Many2one(
        "res.partner",
        "Partner",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    header_html = fields.Text(
        "Header", translate=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    footer_html = fields.Text(
        "Footer", translate=True, readonly=True, states={"draft": [("readonly", False)]}
    )

    state = fields.Selection(
        [("draft", "Draft"), ("valid", "Validated")],
        string="State",
        readonly=True,
        default="draft",
    )

    @api.multi
    def action_validate(self):
        for header in self:
            template_generators = self.env["email.template.gen"].search(
                [("header_id", "=", self.id), ("state", "=", "valid")]
            )
            template_generators.action_validate()

        self.write({"state": "valid"})
        return True

    @api.multi
    def action_reset(self):
        self.write({"state": "draft"})
        return True

    def _render(self, template):
        self.ensure_one()
        partner = self.partner_id
        return self.env["email.template"].render_template_batch(
            template, "res.partner", [partner.id]
        )[partner.id]

    def _get_header(self):
        return self._render(self.header_html)

    def _get_footer(self):
        return self._render(self.footer_html)


class email_template_gen(models.Model):
    _name = "email.template.gen"
    _description = "E-Mail Template Generator"

    name = fields.Char(
        "Name", required=True, readonly=True, states={"draft": [("readonly", False)]}
    )

    header_id = fields.Many2one(
        "email.template.header",
        "Header/Footer",
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    template_id = fields.Many2one(
        "email.template",
        "Template",
        ondelete="set null",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Partner",
        related="header_id.partner_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    subject = fields.Char(
        "Subject",
        translate=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    body_html = fields.Text(
        "Body", translate=True, readonly=True, states={"draft": [("readonly", False)]}
    )

    active = fields.Boolean(
        "Active", default=True, readonly=True, states={"draft": [("readonly", False)]}
    )

    state = fields.Selection(
        [("draft", "Draft"), ("valid", "Validated")],
        string="State",
        readonly=True,
        default="draft",
    )

    no_sanitize = fields.Boolean(
        "No Sanitize",
        help="Don't filter out unsecure elements",
        readonly=True,
        states={"draft": [("readonly", False)]}
    )

    def _assemble(self):
        self.ensure_one()

        parts = []

        def addPart(part):
            if part:
                parts.append(part)

        header = self.header_id
        if header:
            addPart(header._get_header())

        addPart(self.body_html)

        if header:
            addPart(header._get_footer())

        return "\n".join(parts)

    def _transfer(self):
        subject = self.subject
        body_html = self._assemble()
        self.template_id.write({"body_html": body_html, "subject": subject})

    @api.multi
    def action_validate(self):
        if len(self):
            todraft_template_ids = []

            processed_template_ids = set()
            processed_gen_ids = []

            languages = self.env["res.lang"].search([])

            for template_gen in self:
                # check of double activated
                template = template_gen.template_id
                if not template or template.id in processed_template_ids:
                    todraft_template_ids.append(template_gen.id)
                    continue

                # transfer the rest
                for lang in languages:
                    self.browse(template_gen.id).with_context(
                        lang=lang.code, update_template_by_gen=True
                    )._transfer()
                
                processed_template_ids.add(template.id)
                processed_gen_ids.append(template_gen.id)

            if processed_gen_ids:
                self.browse(processed_gen_ids).write({"state": "valid"})

                # check all for double activated
                todraft_template_ids.extend(
                    self.search(
                        [
                            ("template_id", "in", list(processed_template_ids)),
                            ("state", "=", "valid"),
                            ("id", "not in", processed_gen_ids + todraft_template_ids),
                        ]
                    ).ids
                )

            if todraft_template_ids:
                self.browse(todraft_template_ids).write({"state": "draft"})

        return True

    @api.multi
    def action_reset(self):
        self.write({"state": "draft"})
        return True
