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
from openerp.addons.at_base import util
from openerp.addons.at_base import helper
import time
import re

#%(field)s
PATTERN_TEXTSUBST = re.compile("%\(([a-z_.0-9]+)\)[s]")

class subscription_document_fields(osv.osv):
    
    _inherit = "subscription.document.fields"
    _columns = {
        "value": fields.selection([("false","False"),("date","Current Date"), ("text","Text")], "Default Value", size=40, help="Default value is considered for field when new document is generated."),
        "value_text" : fields.text("Text")
    }
    
def _get_document_types(self, cr, uid, context=None):
    cr.execute('select m.model, m.name from subscription_document s, ir_model m WHERE s.model = m.id GROUP BY 1,2')
    return cr.fetchall()

class subscription_subscription(osv.osv):
    
    def model_copy(self, cr, uid, ids, context=None):
        for row in self.read(cr, uid, ids, context=context):
            if not row.get('cron_id',False):
                continue
            cron_ids = [row['cron_id'][0]]
            remaining = self.pool.get('ir.cron').read(cr, uid, cron_ids, ['numbercall'])[0]['numbercall']
            model = None
            try:
                (model_name, oid) = row['doc_source'].split(',')
                oid = int(oid)
                model = self.pool.get(model_name)
            except:
                raise osv.except_osv(_('Wrong Source Document !'), _('Please provide another source document.\nThis one does not exist !'))

            default = {'state':'draft'}
            doc_obj = self.pool.get('subscription.document')
            document_ids = doc_obj.search(cr, uid, [('model.model','=',model_name)])
            doc = doc_obj.browse(cr, uid, document_ids)[0]
            for f in doc.field_ids:
                value=False
                if f.value=='date':
                    value = util.currentDate()
                elif f.value=='text' and f.value_text:                    
                    field_values =  {}
                    curDate = util.currentDate()
                    it = re.finditer(PATTERN_TEXTSUBST, f.value_text)
                    for m in it:
                        field_name = m.group(1)
                        if ( field_name == "year"):
                            field_values[field_name]=util.formatDate(curDate, "%Y")
                        elif (field_name == "month"):
                            field_values[field_name]=util.formatDate(curDate,"%m")
                        elif (field_name == "month_name"):
                            field_values[field_name]=helper.getMonth(cr, uid, curDate, context)
                        else:
                            field_values[field_name]=model.read(cr,uid,oid,[field_name],context)[field_name]                            
                    value = f.value_text % field_values
                                    
                default[f.field.name] = value

            state = 'running'

            # if there was only one remaining document to generate
            # the subscription is over and we mark it as being done
            if remaining == 1:
                state = 'done'
            copy_id = model.copy(cr, uid, oid, default, context)
            self.pool.get('subscription.subscription.history').create(cr, uid, {'subscription_id': row['id'], 'date':time.strftime('%Y-%m-%d %H:%M:%S'), 'document_id': model_name+','+str(copy_id)})
            self.write(cr, uid, [row['id']], {'state':state})
        return True
    
    def _get_source_model(self, cr, uid, context=None):
        return "account.invoice"
    
    _inherit = "subscription.subscription"
    
    _columns = {
        "doc_id" : fields.many2one("subscription.document", "Document type", required=True),
        "doc_source": fields.reference("Source Document", required=True, selection=_get_document_types, size=128, help="User can choose the source document on which he wants to create documents"),
        "doc_source_model" : fields.char("Doc source Model", size=32)
    }

    _defaults = {
        "doc_source_model" : _get_source_model
    }