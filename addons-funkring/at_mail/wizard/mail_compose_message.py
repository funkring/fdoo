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

from openerp.osv import fields, osv
from openerp.addons.at_base.format import LangFormat

class mail_compose_message(osv.TransientModel):
    
     #------------------------------------------------------
    # Template rendering
    #------------------------------------------------------

    def render_message_batch(self, cr, uid, wizard, res_ids, context=None):
        """Generate template-based values of wizard, for the document records given
        by res_ids. This method is meant to be inherited by email_template that
        will produce a more complete dictionary, using Jinja2 templates.

        Each template is generated for all res_ids, allowing to parse the template
        once, and render it multiple times. This is useful for mass mailing where
        template rendering represent a significant part of the process.

        Default recipients are also computed, based on mail_thread method
        message_get_default_recipients. This allows to ensure a mass mailing has
        always some recipients specified.

        :param browse wizard: current mail.compose.message browse record
        :param list res_ids: list of record ids

        :return dict results: for each res_id, the generated template values for
                              subject, body, email_from and reply_to
        """
        subjects = self.render_template_batch(cr, uid, wizard.subject, wizard.model, res_ids, context=context)
        bodies = self.render_template_batch(cr, uid, wizard.body, wizard.model, res_ids, context=context, post_process=True)
        emails_from = self.render_template_batch(cr, uid, wizard.email_from, wizard.model, res_ids, context=context)
        replies_to = self.render_template_batch(cr, uid, wizard.reply_to, wizard.model, res_ids, context=context)

        ctx = dict(context, thread_model=wizard.model)
        default_recipients = self.pool['mail.thread'].message_get_default_recipients(cr, uid, res_ids, context=ctx)
        
        results = dict.fromkeys(res_ids, False)
        for res_id in res_ids:
            results[res_id] = {
                'subject': subjects[res_id],
                'body': bodies[res_id],
                'email_from': emails_from[res_id],
                'reply_to': replies_to[res_id],
            }
            results[res_id].update(default_recipients.get(res_id, dict()))
        return results

    def render_template_batch(self, cr, uid, template, model, res_ids, context=None, post_process=False):
        """ Render the given template text, replace mako-like expressions ``${expr}``
        with the result of evaluating these expressions with an evaluation context
        containing:

            * ``user``: browse_record of the current user
            * ``object``: browse_record of the document record this mail is
                          related to
            * ``context``: the context passed to the mail composition wizard

        :param str template: the template text to render
        :param str model: model name of the document record this mail is related to
        :param list res_ids: list of record ids
        """
        if context is None:
            context = {}
            
        results = dict.fromkeys(res_ids, False)
        langFormat = LangFormat(cr, uid, context=context)
        
        for res_id in res_ids:
            def merge(match):
                exp = str(match.group()[2:-1]).strip()
                result = eval(exp, {
                    'user': self.pool.get('res.users').browse(cr, uid, uid, context=context),
                    'object': self.pool[model].browse(cr, uid, res_id, context=context),
                    'formatLang': langFormat.formatLang,
                    'context': dict(context),  # copy context to prevent side-effects of eval
                })
                return result and tools.ustr(result) or ''
            results[res_id] = template and EXPRESSION_PATTERN.sub(merge, template)
        return results
    
    def _res_ids(self, wizard, context=None):
        mass_mode = wizard.composition_mode in ('mass_mail', 'mass_post')
        if mass_mode and wizard.use_active_domain and wizard.model:
            res_ids = self.pool[wizard.model].search(cr, uid, eval(wizard.active_domain), context=context)
        elif mass_mode and wizard.model and context.get('active_ids'):
            res_ids = context['active_ids']
        else:
            res_ids = [wizard.res_id]
        return res_ids
    
    
    _inherit = "mail.compose.message"

    