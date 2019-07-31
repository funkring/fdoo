# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009-2011 SIA "KN dati". (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from openerp.osv import osv,fields
from report_aeroo import Aeroo_report
from openerp.report.report_sxw import rml_parse
import base64, binascii
from openerp import tools
import encodings
from openerp.tools.translate import _

import imp, sys, os
import time
import zipimport
import logging
from openerp.tools.config import config
import re

_logger = logging.getLogger(__name__)

def cleanFileName(inName):
    repl_map = {
            "Ö" : "Oe",
            "Ü" : "Ue",
            "Ä" : "Ae",
            "ö" : "oe",
            "ü" : "ue",
            "ä" : "ae"
    }
    for key,value in repl_map.iteritems():
        inName = inName.replace(key,value)
    inName = inName.replace(", ","_")
    inName = inName.replace(" ","_")
    inName = re.sub("[^a-zA-Z0-9\-_ ,]","",inName)
    return inName

class report_stylesheets(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'report.stylesheets'
    _description = 'Report Stylesheets'

    def _report_styles_fname(self, cr, uid, ids, field_name, arg, context=None):
      res = dict.fromkeys(ids)
      for obj in self.browse(cr, uid, ids, context):
        res[obj.id] = "%s.odt" % cleanFileName(obj.name)
      return res

    _columns = {
        'name':fields.char('Name', size=64, required=True),
        'report_styles' : fields.binary('Template Stylesheet', help='OpenOffice.org stylesheet (.odt)'),
        'report_styles_fname': fields.function(_report_styles_fname, type="char", string="Report Filename", store=False, readonly=True)

    }


class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'

    _columns = {
        #'report_styles' : fields.binary('Report Styles', help='OpenOffice stylesheet (.odt)'),
        'stylesheet_id': fields.many2one('report.stylesheets', 'Aeroo Global Stylesheet'),
        'stylesheet_landscape_id': fields.many2one('report.stylesheets', 'Aeroo Global Landscape Stylesheet'),
        'stylesheet_intern_id' : fields.many2one('report.stylesheets', 'Aeroo Intern Stylesheet'),
        'stylesheet_intern_landscape_id' : fields.many2one('report.stylesheets', 'Aeroo Intern Landscape Stylesheet')
    }


class report_mimetypes(osv.osv):
    '''
    Aeroo Report Mime-Type
    '''
    _name = 'report.mimetypes'
    _description = 'Report Mime-Types'

    _columns = {
        'name':fields.char('Name', size=64, required=True, readonly=True),
        'code':fields.char('Code', size=16, required=True, readonly=True),
        'compatible_types':fields.char('Compatible Mime-Types', size=128, readonly=True),
        'filter_name':fields.char('Filter Name', size=128, readonly=True),
        'extension' : fields.char('Extension',readonly=True),
        'mimetype' : fields.char('Mimetype',readonly=True)
    }


class Report(osv.Model):
    
    def _get_report_from_name(self, cr, uid, report_name):
        """Get the first record of ir.actions.report.xml having the ``report_name`` as value for
        the field report_name.
        """
        report_obj = self.pool['ir.actions.report.xml']
        qwebtypes = ['aeroo', 'qweb-pdf', 'qweb-html']
        conditions = [('report_type', 'in', qwebtypes), ('report_name', '=', report_name)]
        idreport = report_obj.search(cr, uid, conditions)[0]
        return report_obj.browse(cr, uid, idreport)
    
    _inherit = "report"
    

class report_xml(osv.osv):
    _inherit = 'ir.actions.report.xml'

    def load_from_file(self, path, dbname, key):
        class_inst = None
        expected_class = 'Parser'

        ad = os.path.abspath(os.path.join(tools.ustr(config['root_path']), u'addons'))
        mod_path_list = map(lambda m: os.path.abspath(tools.ustr(m.strip())), config['addons_path'].split(','))
        mod_path_list.append(ad)

        for mod_path in mod_path_list:
            if os.path.lexists(mod_path+os.path.sep+path.split(os.path.sep)[0]):
                filepath=mod_path+os.path.sep+path
                filepath = os.path.normpath(filepath)
                
                python_path = os.path.dirname(filepath)
                if not python_path in sys.path:
                  sys.path.append(python_path)
                  
                mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
                mod_name = '%s_%s_%s' % (dbname,mod_name,key)

                if file_ext.lower() == '.py':
                    py_mod = imp.load_source(mod_name, filepath)

                elif file_ext.lower() == '.pyc':
                    py_mod = imp.load_compiled(mod_name, filepath)

                if expected_class in dir(py_mod):
                    class_inst = py_mod.Parser
                return class_inst
            elif os.path.lexists(mod_path+os.path.sep+path.split(os.path.sep)[0]+'.zip'):
                zimp = zipimport.zipimporter(mod_path+os.path.sep+path.split(os.path.sep)[0]+'.zip')
                return zimp.load_module(path.split(os.path.sep)[0]).parser.Parser
        return None

    def load_from_source(self, source):
        expected_class = 'Parser'
        context = {'Parser':None}
        try:
            exec source in context
            return context['Parser']
        except Exception, e:
            return None

    def _lookup_report(self, cr, name):
        cr.execute("SELECT * FROM ir_act_report_xml WHERE report_type = 'aeroo' AND report_name = %s AND active='t'", (name,))
        records = cr.dictfetchall()
        for record in records:
            parser=rml_parse
            if record['parser_state']=='loc' and record['parser_loc']:
                parser=self.load_from_file(record['parser_loc'], cr.dbname, record['id']) or parser
            elif record['parser_state']=='def' and record['parser_def']:
                parser=self.load_from_source("from report import report_sxw\n"+record['parser_def']) or parser
            return Aeroo_report(cr, "report."+name, record['model'], record['report_rml'],parser)
        return super(report_xml,self)._lookup_report(cr, name)

    def _get_encodings(self, cursor, user, context={}):
        l = list(set(encodings._aliases.values()))
        l.sort()
        return zip(l, l)
        
    def change_input_format(self, cr, uid, ids, in_format):
        out_format = self.pool.get('report.mimetypes').search(cr, uid, [('code','=',in_format)])
        return {
            'value':{'out_format': out_format and out_format[0] or False}
        }

    def _get_in_mimetypes(self, cr, uid, context={}):
        obj = self.pool.get('report.mimetypes')
        ids = obj.search(cr, uid, [('filter_name','=',False)], context=context)
        res = obj.read(cr, uid, ids, ['code', 'name'], context)
        return [(r['code'], r['name']) for r in res] + [('','')]

    def _get_attachment_name(self, cr, uid, report, obj, ext=None, context=None):
        attach = report.attachment
        aname = attach and eval(attach, {'object':obj, 'time':time}) or False
        if not aname:
            return None, None
        #create file name
        extension = ext or report.out_format.extension or "pdf"
        fname = aname
        if not fname.endswith(extension):
            fname = "%s.%s" % (fname,extension)
        return aname, fname

    def _get_attachment_id(self, cr, uid, report, obj, context=None):
        aname, fname = self._get_attachment_name(cr, uid, report, obj, context=context)
        if fname:
            return self.pool.get("ir.attachment").search_id(cr, uid, [("datas_fname","=",fname),("res_model","=",obj._model._name),("res_id","=",obj.id)])
        return None

    def _write_attachment(self, cr, uid, report, obj, attachment_id=None, datas=None, data=None, ext=None, origin=None, context=None):
        aname, fname = self._get_attachment_name(cr, uid, report, obj, ext=ext, context=context)
        if aname:
            values = {
                "name": aname,
                "datas": datas or (data and base64.encodestring(data)) or None,
                "datas_fname": fname,
                "res_model": obj._model._name,
                "res_id": obj.id
            }
            if origin:
                values["origin"] = origin
            if attachment_id:
                self.pool.get("ir.attachment").write(cr,uid,attachment_id,values,context=context)
            else:
                attachment_id = self.pool.get("ir.attachment").create(cr,uid,values,context=context)
            return attachment_id
        return False

    def _get_report_obj(self, cr, uid, res_model, res_id, report_name=None, context=None):
        if not report_name:
            report_name=res_model

        report_id = self.search_id(cr, uid, [("report_name","=",report_name)])
        if not report_id:
            raise osv.except_osv(_("Error!"), _("No report with report_name=%s found") % report_name)

        report = self.browse(cr, uid, report_id, context)
        if not report.attachment:
            raise osv.except_osv(_("Error!"), _("Attachments not defined for report %s") % report.name)

        model = self.pool.get(res_model)
        if not model:
            raise osv.except_osv(_("Error!"), _("Model %s not found") % res_model)

        obj = model.browse(cr,uid,res_id,context=context)
        return report, obj

    def write_attachment(self, cr, uid, res_model, res_id, report_name=None, datas=None, data=None, origin=None, context=None):
        report, obj = self._get_report_obj(cr, uid, res_model, res_id, report_name, context)
        attachment_id = self._get_attachment_id(cr, uid, report, obj, context=context)
        return self._write_attachment(cr, uid, report, obj, attachment_id=attachment_id, datas=datas, data=data, origin=origin, context=context)

    def get_attachment_id(self, cr, uid, res_model, res_id, report_name=None, context=None):
        report, obj = self._get_report_obj(cr, uid, res_model, res_id, report_name, context)
        return self._get_attachment_id(cr, uid, report, obj, context=context)

    def _get_replacement(self, cr, uid, obj, report_xml, context=None):
        """
        @return tuple with (report,template_data) 
        """
        return (None,None)

    _columns = {
        'charset':fields.selection(_get_encodings, string='Charset', required=True),
        'styles_mode': fields.selection([
            ('default','Not used'),
            ('global', 'Global'),
            ('global_landscape','Global (Landscape)'),
            ('intern', 'Intern'),
            ('intern_landscape','Intern (Landscape)'),
            ('specified', 'Specified'),
            ], string='Stylesheet'),
        #'report_styles' : fields.binary('Template Styles', help='OpenOffice stylesheet (.odt)'),
        'stylesheet_id':fields.many2one('report.stylesheets', 'Template Stylesheet'),
        'preload_mode':fields.selection([
            ('static','Static'),
            ('preload','Preload'),
        ],'Preload Mode'),
        'tml_source':fields.selection([
            ('database','Database'),
            ('file','File'),
            ('parser','Parser'),
        ],'Template source', select=True),
        'parser_def': fields.text('Parser Definition'),
        'parser_loc':fields.char('Parser location', size=128, help="Path to the parser location. Beginning of the path must be start with the module name!\nLike this: {module name}/{path to the parser.py file}"),
        'parser_state':fields.selection([
            ('default','Default'),
            ('def','Definition'),
            ('loc','Location'),
        ],'State of Parser', select=True),
        'in_format': fields.selection(_get_in_mimetypes, 'Template Mime-type'),
        'out_format':fields.many2one('report.mimetypes', 'Output Mime-type'),
        'active':fields.boolean('Active'),
        'process_sep':fields.boolean('Process separately'),
        'user_defined' : fields.boolean('User Defined')
    }

    def unlink(self, cr, uid, ids, context=None):
        #TODO: process before delete resource
        trans_obj = self.pool.get('ir.translation')
        trans_ids = trans_obj.search(cr, uid, [('type','=','report'),('res_id','in',ids)])
        trans_obj.unlink(cr, uid, trans_ids)
        ####################################
        reports = self.read(cr, uid, ids, ['report_name','model'])
        for r in reports:
            ir_value_ids = self.pool.get('ir.values').search(cr, uid, [('name','=',r['report_name']),
                                                                            ('value','=','ir.actions.report.xml,%s' % r['id']),
                                                                            ('model','=',r['model'])
                                                                            ])
        model_data_obj = self.pool.get('ir.model.data')
        model_data_ids = model_data_obj.search(cr, uid, [('model','=','ir.actions.report.xml'),('res_id','in',ids)])
        self.pool.get('ir.model.data').unlink(cr, uid, model_data_ids)

        ####################################
        res = super(report_xml, self).unlink(cr, uid, ids, context)
        return res


    def write(self, cr, user, ids, vals, context=None):
        if 'report_sxw_content_data' in vals:
            if vals['report_sxw_content_data']:
                try:
                    base64.decodestring(vals['report_sxw_content_data'])
                except binascii.Error:
                    vals['report_sxw_content_data'] = False
        if type(ids)==list:
            ids = ids[0]
        res = super(report_xml, self).write(cr, user, ids, vals, context)
        return res

    def _set_auto_false(self, cr, uid, ids=[]):
        if not ids:
            ids = self.search(cr, uid, [('report_type','=','aeroo'),('auto','=','True')])
        for id in ids:
            self.write(cr, uid, id, {'auto':False})

    def _get_default_outformat(self, cr, uid, context):
        obj = self.pool.get('report.mimetypes')
        res = obj.search(cr, uid, [('code','=','oo-odt')])
        return res and res[0] or False

    _defaults = {
        'tml_source': 'database',
        'in_format' : 'oo-odt',
        'out_format' : _get_default_outformat,
        'charset': 'ascii',
        'styles_mode' : 'default',
        'preload_mode': 'static',
        'parser_state': 'default',
        'parser_def': """class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({})""",
        'active' : True,
    }

