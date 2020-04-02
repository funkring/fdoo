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

import openerp.report
from openerp import tools, api

from openerp.osv import fields, osv
from openerp.addons.at_base.format import LangFormat


class email_template(osv.osv):
    _inherit = "email.template"
    
    def _is_generated(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, False)
        cr.execute("""SELECT t.id 
            FROM email_template t
            INNER JOIN email_template_gen g ON g.template_id = t.id
            WHERE t.id IN %s
              AND g.state = 'valid'
              AND g.active
        """, (tuple(ids),))
        
        for (template_id, ) in cr.fetchall():
            res[template_id] = True
        return res
    
    def _no_sanitize(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, False)
        cr.execute("""SELECT t.id 
            FROM email_template t
            INNER JOIN email_template_gen g ON g.template_id = t.id
            WHERE t.id IN %s
              AND g.state = 'valid'
              AND g.active
              AND g.no_sanitize
        """, (tuple(ids),))

        for (template_id, ) in cr.fetchall():
            res[template_id] = True
        return res
        
    
    _columns = {
        "template_gen_ids": fields.one2many("email.template.gen", "template_id", "Template Generators"),
        "is_generated": fields.function(_is_generated, type="boolean", string="Generated", store=False),
        "no_sanitize": fields.function(_is_generated, type="boolean", string="No Sanitize", store=False)
    }

    def _get_render_env(self, cr, uid, template, model, res_ids, variables, context=None):
        variables = super(email_template, self)._get_render_env(
            cr, uid, template, model, res_ids, variables, context=context
        )
        langFormat = LangFormat(cr, uid, context=context)
        variables["formatLang"] = langFormat.formatLang
        return variables

    def generate_email_batch(self, cr, uid, template_id, res_ids, context=None, fields=None):
        """Generates an email from the template for given the given model based on
        records given by res_ids.
        
        :param template_id: id of the template to render.
        :param res_id: id of the record to use for rendering the template (model
                       is taken from template definition)
        :returns: a dict containing all relevant fields for creating a new
                  mail.mail entry, with one extra key ``attachments``, in the
                  format [(report_name, data)] where data is base64 encoded.
        """
        if context is None:
            context = {}
        if fields is None:
            fields = [
                "subject",
                "body_html",
                "email_from",
                "email_to",
                "partner_to",
                "email_cc",
                "reply_to",
            ]

        report_xml_pool = self.pool.get("ir.actions.report.xml")
        res_ids_to_templates = self.get_email_template_batch(
            cr, uid, template_id, res_ids, context
        )

        # templates: res_id -> template; template -> res_ids
        templates_to_res_ids = {}
        for res_id, template in res_ids_to_templates.iteritems():
            templates_to_res_ids.setdefault(template, []).append(res_id)


        results = dict()
        for template, template_res_ids in templates_to_res_ids.iteritems():
            # generate fields value for all res_ids linked to the current template
            no_sanitize = template.no_sanitize
            
            ctx = context.copy()
            if template.lang:
                ctx["lang"] = template._context.get("lang")
            for field in fields:
                generated_field_values = self.render_template_batch(
                    cr,
                    uid,
                    getattr(template, field),
                    template.model,
                    template_res_ids,
                    post_process=(field == "body_html"),
                    context=ctx,
                )
                for res_id, field_value in generated_field_values.iteritems():
                    results.setdefault(res_id, dict())[field] = field_value
            # compute recipients
            results = self.generate_recipients_batch(
                cr, uid, results, template.id, template_res_ids, context=context
            )
            # update values for all res_ids
            for res_id in template_res_ids:
                values = results[res_id]
                # body: add user signature, sanitize
                if "body_html" in fields and template.user_signature:
                    signature = (
                        self.pool.get("res.users")
                        .browse(cr, uid, uid, context)
                        .signature
                    )
                    if signature:
                        values["body_html"] = tools.append_content_to_html(
                            values["body_html"], signature, plaintext=False
                        )
                if values.get("body_html"):
                    if no_sanitize:
                        values["body"] = values["body_html"]
                        #body_text = tools.html2plaintext(tools.html_sanitize(values["body_html"]))
                        #values["body_alternative"] = body_text
                    else:
                        values["body"] = tools.html_sanitize(values["body_html"])

                # technical settings
                values.update(
                    mail_server_id=template.mail_server_id.id or False,
                    auto_delete=template.auto_delete,
                    model=template.model,
                    res_id=res_id or False,
                    attachment_ids=[attach.id for attach in template.attachment_ids],
                )

            # Add report in attachments: generate once for all template_res_ids
            if template.report_template:
                for res_id in template_res_ids:
                    attachments = []
                    report_name = self.render_template(
                        cr,
                        uid,
                        template.report_name,
                        template.model,
                        res_id,
                        context=ctx,
                    )
                    report = report_xml_pool.browse(
                        cr, uid, template.report_template.id, context
                    )
                    report_service = report.report_name

                    if report.report_type in ["qweb-html", "qweb-pdf"]:
                        result, format = (
                            self.pool["report"].get_pdf(
                                cr, uid, [res_id], report_service, context=ctx
                            ),
                            "pdf",
                        )
                    else:
                        result, format = openerp.report.render_report(
                            cr,
                            uid,
                            [res_id],
                            report_service,
                            {"model": template.model},
                            ctx,
                        )

                    # TODO in trunk, change return format to binary to match message_post expected format
                    result = base64.b64encode(result)
                    if not report_name:
                        report_name = "report." + report_service
                    ext = "." + format
                    if not report_name.endswith(ext):
                        report_name += ext
                    attachments.append((report_name, result))
                    results[res_id]["attachments"] = attachments

        return results
