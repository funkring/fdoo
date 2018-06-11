# -*- encoding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2009-2011 Alistek, SIA. (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
# Copyright (C) 2009  Domsense s.r.l.
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

import os, sys, traceback
import tempfile
from openerp import report
from openerp.report.report_sxw import report_sxw, report_rml
from pyPdf import PdfFileWriter, PdfFileReader
#import zipfile
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from xml.dom import minidom
import base64
from openerp.osv import osv
from openerp.tools.translate import _
from openerp import tools
import time
import re
import copy

import openerp.modules as addons
from openerp import release

import aeroolib
from aeroolib.plugins.opendocument import Template, OOSerializer
from genshi.template import NewTextTemplate
from openerp.modules.registry import RegistryManager

import logging
logger = logging.getLogger(__name__)

from ExtraFunctions import ExtraFunctions

AEROO_TIMEOUT = 1
AEROO_RETRIES = 3

def fixPdf(data,ret_reader=False):
    if data:
        try:
            reader = PdfFileReader(StringIO(data))
            if ret_reader:
                return reader
            return data
        except Exception, e:
            error = hasattr(e, "message") and e.message or ""
            logger.error("PDF corrupted and should be fixed: %s",error)
            if os.path.exists("/usr/bin/pdftk"):
                pdfFile = None
                pdfFileFixed = None
                try:
                    pdfFile = tempfile.mktemp(".pdf")
                    fp = open(pdfFile,"wb")
                    try:
                        fp.write(data)
                    finally:
                        fp.close()

                    pdfFileFixed = tempfile.mktemp(".pdf", "fixed")
                    cmd = "pdftk %s output %s" % (pdfFile,pdfFileFixed)
                    cmd_fp = os.popen(cmd,"r",1)
                    try:
                        logger.info("PDF Fixed %s",cmd_fp.read())
                    finally:
                        cmd_fp.close()

                    if os.path.exists(pdfFileFixed):
                        data_fp = open(pdfFileFixed,"r")
                        try:
                            data = data_fp.read()
                        finally:
                            data_fp.close()

                        reader = PdfFileReader(StringIO(data))
                        if ret_reader:
                            return reader
                        return data
                finally:
                    if pdfFile and os.path.exists(pdfFile):
                        os.remove(pdfFile)
                    if pdfFileFixed and os.path.exists(pdfFileFixed):
                        os.remove(pdfFileFixed)
    return None


class Counter(object):
    def __init__(self, name, start=0, interval=1):
        self.name = name
        self._number = start
        self._interval = interval

    def next(self):
        curr_number = self._number
        self._number += self._interval
        return curr_number

    def get_inc(self):
        return self._number

    def prev(self):
        return self._number-self._interval

class Aeroo_report(report_sxw):

    def __init__(self, cr, name, table, rml=False, parser=False, header=True, store=False):
        super(Aeroo_report, self).__init__(name, table, rml, parser, header, store, register=False)
        self.oo_subreports = []
        self.epl_images = []
        self.counters = {}

        pool = RegistryManager.get(cr.dbname)
        ir_obj = pool.get('ir.actions.report.xml')
        report_xml_ids = ir_obj.search(cr, 1, [('report_name', '=', self.name2)])
        if report_xml_ids:
            report_xml = ir_obj.browse(cr, 1, report_xml_ids[0])
        else:
            report_xml = False

        if report_xml and report_xml.preload_mode == 'preload':
            file_data = report_xml.report_sxw_content
            if not file_data:
                logger.warn("template is not defined in %s (%s) !" % (name, table))
                template_io = None
            else:
                template_io = StringIO()
                template_io.write(base64.decodestring(file_data))
                style_io=self.get_styles_file(cr, 1, report_xml)
            if template_io:
                self.serializer = OOSerializer(template_io, oo_styles=style_io)

    #def __del__(self):
    #    self._cleanup_subreports()

    def getObjects_mod(self, cr, uid, ids, report_xml, context, parser=None):
        if parser and hasattr(parser,"_load_objects"):
            return parser._load_objects(cr, uid, ids, report_xml, context)
        table_obj = RegistryManager.get(cr.dbname).get(self.table)
        return table_obj.browse(cr, uid, ids, context=context)
    
    def _onResult(self, cr, uid, objs, res, context=None):
        report_meta = None
        if not context is None:
            report_meta = context.get("report_meta")
        if not report_meta is None and objs and len(objs) == 1 and objs[0]._model:
            obj = objs[0]
            obj_name = None
            
            if hasattr(obj._model,"report_name_get"):
                obj_name = obj._model.report_name_get(cr, uid, [obj.id], context=context)[0][1]
            else:
                obj_name = obj._model.name_get(cr, uid, [obj.id], context=context)[0][1]
                
            if obj_name:
                obj_name = obj_name.strip()
                
            if obj_name:
                first_name = report_meta.get("name")            
                if not first_name:
                    report_meta["name"] = obj_name 
                else:
                    report_meta["name"] = min(obj_name,first_name)
                    
                last_name = report_meta.get("last_name")
                if not last_name:
                    report_meta["last_name"] = obj_name
                else:
                    report_meta["last_name"] = max(obj_name,last_name)
                
        return res

    ##### Counter functions #####
    def _def_inc(self, name, start=0, interval=1):
        self.counters[name] = Counter(name, start, interval)

    def _get_inc(self, name):
        return self.counters[name].get_inc()

    def _prev(self, name):
        return self.counters[name].prev()

    def _next(self, name):
        return self.counters[name].next()
    #############################

    def _epl_asimage(self, data):
        from PIL import Image
        from math import ceil
        if not data:
            return ''
        img = Image.open(StringIO(base64.decodestring(data)))
        if img.format!='BMP':
            return ''
        data = base64.decodestring(data)[62:]
        line_len = int(ceil(img.size[0]/32.0)*4)
        temp_data = ''
        for n in range(img.size[1]):
            curr_pos = n*line_len
            temp_data = data[curr_pos:curr_pos+line_len][:int(img.size[0]/8)] + temp_data

        new_data = ''
        for d in temp_data:
            new_data += chr(ord(d)^255)
        self.epl_images.append(new_data)
        return img.size

    def _epl2_gw(self, start_x, start_y, data):
        if not data:
            return None
        size_x, size_y = self._epl_asimage(data)
        return 'GW'+str(start_x)+','+str(start_y)+','+str(int(size_x/8))+','+str(size_y)+',<binary_data>'

    def _include_document(self, aeroo_ooo=False):
        def include_document(data, silent=False):
            if not aeroo_ooo:
                return _("Error! Include document not available!")
            import binascii, urllib2
            dummy_fd, temp_file_name = tempfile.mkstemp(suffix='.odt', prefix='aeroo-report-')
            temp_file = open(temp_file_name, 'wb')
            if os.path.isfile(data):
                fd = file(data, 'rb')
                data = fd.read()
            else:
                error = False
                try:
                    url_file = urllib2.urlopen(data)
                    data = url_file.read()
                except urllib2.HTTPError:
                    os.unlink(temp_file_name)
                    error = _('HTTP Error 404! Not file found:')+' %s' % data
                except urllib2.URLError, e:
                    os.unlink(temp_file_name)
                    error = _('Error!')+' %s' % e
                except IOError, e:
                    os.unlink(temp_file_name)
                    error = _('Error!')+' %s' % e
                except Exception, e:
                    try:
                        data = base64.decodestring(data)
                    except binascii.Error:
                        os.unlink(temp_file_name)
                        error = _('Error! Not file found:')+' %s' % data
                if error:
                    if not silent:
                        return error
                    else:
                        return None
            try:
                temp_file.write(data)
            finally:
                temp_file.close()
            self.oo_subreports.append(temp_file_name)
            return "<insert_doc('%s')>" % temp_file_name
        return include_document

    def _subreport(self, cr, uid, output='odt', aeroo_ooo=False, context={}):
        pool = RegistryManager.get(cr.dbname)
        ir_obj = pool.get('ir.actions.report.xml')
        #### for odt documents ####
        def odt_subreport(name=None, obj=None, data=None):
            if not aeroo_ooo:
                return _("Error! Subreports not available!")
            report_xml_ids = ir_obj.search(cr, uid, [('report_name', '=', name)], context=context)
            if report_xml_ids:
                report_xml = ir_obj.browse(cr, uid, report_xml_ids[0], context=context)
                # if no param was passed set 
                # report action
                if not obj:
                    obj = report_xml
                
                report = None
                report_format = None
                
                # update data
                tdata = {'model': obj._model._name, 
                         'id': obj.id, 
                         'report_type': report_xml.report_type, 
                         'in_format': report_xml.in_format
                        }
                if data:
                    tdata.update(data)
                    
                # set data
                data = tdata
                 
                # aeroo report
                if report_xml.report_type == "aeroo":
                    reportInstance = ir_obj._lookup_report(cr, name)
                    report, report_format = reportInstance.create_aeroo_report(cr, uid, \
                                                [obj.id], data, report_xml, context=context, output='odt') # change for OpenERP 6.0 - Service class usage
                
                # html report
                else:
                    report_format = "html"
                    report = pool["report"].get_html(cr, uid, [obj.id], name, data=data, context=context)
                    
                # create 
                if report:
                    dummy_fd, temp_file_name = tempfile.mkstemp(suffix="."+report_format, prefix="aeroo-report-")
                    temp_file = open(temp_file_name, "wb")
                    try:
                        temp_file.write(report)
                    finally:
                        temp_file.close()
                            
                    self.oo_subreports.append(temp_file_name)
                    return "<insert_doc('%s')>" % temp_file_name
                
            return None
        #### for text documents ####
        def raw_subreport(name=None, obj=None):
            report_xml_ids = ir_obj.search(cr, uid, [('report_name', '=', name)], context=context)
            if report_xml_ids:
                report_xml = ir_obj.browse(cr, uid, report_xml_ids[0], context=context)
                data = {'model': obj._table_name, 'id': obj.id, 'report_type': 'aeroo', 'in_format': 'genshi-raw'}

                reportInstance = ir_obj._lookup_report(cr, name)
                report, output = reportInstance.create_genshi_raw_report(cr, uid, \
                                            [obj.id], data, report_xml, context=context, output=output) # change for OpenERP 6.0 - Service class usage
                return report
            return None

        if output=='odt':
            return odt_subreport
        elif output=='raw':
            return raw_subreport

    def _cleanup_subreports(self):
        while self.oo_subreports:
            sub_report = self.oo_subreports.pop()
            try:
                os.unlink(sub_report)
            except:
                logger.warn("Unable to cleanup %s" % sub_report)

    def set_xml_data_fields(self, objects, parser):
        xml_data_fields = parser.localcontext.get('xml_data_fields', False)
        if xml_data_fields:
            for field in xml_data_fields:
                for o in objects:
                    if getattr(o, field):
                        xml_data = base64.decodestring(getattr(o, field))
                        xmldoc = minidom.parseString(xml_data)
                        setattr(o, field, xmldoc.firstChild)
        return objects

    def get_other_template(self, cr, uid, data, parser):
        if hasattr(parser, 'get_template'):
            pool = RegistryManager.get(cr.dbname)
            record = pool.get(data['model']).browse(cr, uid, data['id'], {})
            template = parser.get_template(cr, uid, record)
            return template
        else:
            return False

    def get_styles_file(self, cr, uid, report_xml, context=None):
        pool = RegistryManager.get(cr.dbname)
        style_io=None
        styles_mode = report_xml.styles_mode
        if styles_mode != 'default':
            style_content = None

            if styles_mode == 'intern':
                company_id = pool.get('res.users')._get_company(cr, uid, context=context)
                style_content = pool.get('res.company').browse(cr, uid, company_id, context=context).stylesheet_intern_id
                style_content = style_content and style_content.report_styles or False
                if not style_content:
                    styles_mode='global'
            elif styles_mode == 'intern_landscape':
                company_id = pool.get('res.users')._get_company(cr, uid, context=context)
                style_content = pool.get('res.company').browse(cr, uid, company_id, context=context).stylesheet_intern_landscape_id
                style_content = style_content and style_content.report_styles or False
                if not style_content:
                    styles_mode='global_landscape'

            if not style_content:
                if styles_mode=='global':
                    company_id = pool.get('res.users')._get_company(cr, uid, context=context)
                    style_content = pool.get('res.company').browse(cr, uid, company_id, context=context).stylesheet_id
                    style_content = style_content and style_content.report_styles or False
                elif styles_mode=='global_landscape':
                    company_id = pool.get('res.users')._get_company(cr, uid, context=context)
                    style_content = pool.get('res.company').browse(cr, uid, company_id, context=context).stylesheet_landscape_id
                    style_content = style_content and style_content.report_styles or False
                elif styles_mode=='specified':
                    style_content = report_xml.stylesheet_id
                    style_content = style_content and style_content.report_styles or False

            if style_content:
                style_io = StringIO()
                style_io.write(base64.decodestring(style_content))
        return style_io

    def create_genshi_raw_report(self, cr, uid, ids, data, report_xml, context=None, output='raw'):
        def preprocess(data):
            self.epl_images.reverse()
            while self.epl_images:
                img = self.epl_images.pop()
                data = data.replace('<binary_data>', img, 1)
            return data.replace('\n', '\r\n')

        if context is None:
            context={}
        else:
            context = context.copy()
        
        # get parser and objects
        oo_parser = self.parser(cr, uid, self.name2, context=context)
        objects = self.getObjects_mod(cr, uid, ids, report_xml, context, parser=oo_parser)
        oo_parser.objects = objects
        
        self.set_xml_data_fields(objects, oo_parser) # Get/Set XML
        oo_parser.localcontext['objects'] = objects
        oo_parser.localcontext['data'] = data
        oo_parser.localcontext['user_lang'] = context.get('lang', False)
        if len(objects)>0:
            oo_parser.localcontext['o'] = objects[0]
        xfunc = ExtraFunctions(cr, uid, report_xml.id, oo_parser.localcontext)
        oo_parser.localcontext.update(xfunc.functions)
        file_data = self.get_other_template(cr, uid, data, oo_parser) or report_xml.report_sxw_content # Get other Tamplate
        ################################################
        if not file_data:
            return False, output

        oo_parser.localcontext['include_subreport'] = self._subreport(cr, uid, output='raw', aeroo_ooo=False, context=context)
        oo_parser.localcontext['epl2_gw'] = self._epl2_gw

        self.epl_images = []
        basic = NewTextTemplate(source=base64.decodestring(file_data))

        data = preprocess(basic.generate(**oo_parser.localcontext).render().decode('utf8').encode(report_xml.charset))
        return self._onResult(cr, uid, objects, (data, output), context=context)

    def _aeroo_ooo_test(self, cr):
        '''
        Detect report_aeroo_ooo module
        '''
        aeroo_ooo = False
        cr.execute("SELECT id, state FROM ir_module_module WHERE name='report_aeroo_ooo'")
        helper_module = cr.dictfetchone()
        if helper_module and helper_module['state'] in ('installed', 'to upgrade'):
            aeroo_ooo = True
        return aeroo_ooo

    def create_aeroo_report(self, cr, uid, ids, data, report_xml, context=None, output='odt', style_io=None):
        """ Returns an aeroo report generated with aeroolib
        """
        pool = RegistryManager.get(cr.dbname)
        if context is None:
            context={}
        else:
            context = context.copy()
            
        if self.name=='report.printscreen.list':
            context['model'] = data['model']
            context['ids'] = ids

        # create parser
        oo_parser = self.parser(cr, uid, self.name2, context=context)
        objects = not context.get('no_objects', False) and self.getObjects_mod(cr, uid, ids, report_xml, context, parser=oo_parser) or []
        report_obj = pool.get("ir.actions.report.xml")
        
        # check for report forward
        if hasattr(oo_parser,"_report_forward"):          
          report_forward = oo_parser._report_forward(objects)
          if report_forward:
            report_forward_inst = report_obj._lookup_report(cr, report_forward["name"])
            forward_report_data, forward_report_format = report_forward_inst.create(cr, uid, report_forward["ids"], data, context)
            return self._onResult(cr, uid, objects, (forward_report_data, forward_report_format), context=context)
          
        # report replacement
        if objects and len(objects) == 1:            
            # get replacement
            repl_report_xml, style_io = report_obj._get_replacement(cr, uid, objects[0], report_xml, context=context)
            if repl_report_xml:
                return self.create_aeroo_report(cr, uid, ids, data, repl_report_xml, context=context, output=output, style_io=style_io)


        oo_parser.objects = objects
        self.set_xml_data_fields(objects, oo_parser) # Get/Set XML

        oo_parser.localcontext['objects'] = objects
        oo_parser.localcontext['data'] = data
        oo_parser.localcontext['user_lang'] = context.get('lang', False)
        if len(objects)==1:
            oo_parser.localcontext['o'] = objects[0]
        xfunc = ExtraFunctions(cr, uid, report_xml.id, oo_parser.localcontext)
        oo_parser.localcontext.update(xfunc.functions)
        
        # get style
        if not style_io:
            style_io=self.get_styles_file(cr, uid, report_xml, context)
        
        # get template
        if report_xml.tml_source in ('file', 'database'):
            file_data = base64.decodestring(report_xml.report_sxw_content)
        else:
            file_data = self.get_other_template(cr, uid, data, oo_parser)
        if not file_data and not report_xml.report_sxw_content:
            return False, output
        else:
            if report_xml.preload_mode == 'preload' and hasattr(self, 'serializer'):
                serializer = copy.copy(self.serializer)
                serializer.apply_style(style_io)
                template_io = serializer.template
            else:
                template_io = StringIO()
                template_io.write(file_data or base64.decodestring(report_xml.report_sxw_content) )
                serializer = OOSerializer(template_io, oo_styles=style_io)
            basic = Template(source=template_io, serializer=serializer)

        aeroo_ooo = context.get('aeroo_ooo', False)
        oo_parser.localcontext['include_subreport'] = self._subreport(cr, uid, output='odt', aeroo_ooo=aeroo_ooo, context=context)
        oo_parser.localcontext['include_document'] = self._include_document(aeroo_ooo)

        ####### Add counter functons to localcontext #######
        oo_parser.localcontext.update({'def_inc':self._def_inc,
                                      'get_inc':self._get_inc,
                                      'prev':self._prev,
                                      'next':self._next})

        user_name = pool.get('res.users').browse(cr, uid, uid, {}).name

        report_tile = report_xml.name
        eval_model = data.get("model",context.get("active_model"))        
        if eval_model:
            modeldef_obj = pool.get('ir.model')
            modeldef_id = modeldef_obj.search(cr, uid, [('model','=',eval_model)])[0]            
            report_title = modeldef_obj.browse(cr, uid, modeldef_id).name

        #basic = Template(source=None, filepath=odt_path)

        basic.Serializer.add_title(report_tile)
        basic.Serializer.add_creation_user(user_name)
        version = addons.load_information_from_description_file('report_aeroo')['version']
        basic.Serializer.add_generator_info('Aeroo Lib/%s Aeroo Reports/%s' % (aeroolib.__version__, version))
        basic.Serializer.add_custom_property('Aeroo Reports %s' % version, 'Generator')
        basic.Serializer.add_custom_property('OpenERP %s' % release.version, 'Software')
        basic.Serializer.add_custom_property('http://www.alistek.com/', 'URL')
        basic.Serializer.add_creation_date(time.strftime('%Y-%m-%dT%H:%M:%S'))

        try:
            data = basic.generate(**oo_parser.localcontext).render().getvalue()
        except Exception, e:
            tb_s = reduce(lambda x, y: x+y, traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
            logger.error(tb_s)
            self._cleanup_subreports()
            raise Exception(_("Aeroo Reports: Error while generating the report."), e, str(e), _("For more reference inspect error logs."))

        ######### OpenOffice extras #########
        if (output!=report_xml.in_format[3:] or self.oo_subreports):
            if aeroo_ooo:
                # build sub report
                def build_report(data,retry=AEROO_RETRIES):
                    with report_obj._new_ooproxy(cr, uid, context=context) as DC:
                        try:
                            DC.putDocument(data)
                            if self.oo_subreports:
                                DC.insertSubreports(self.oo_subreports)
                            return DC.readDocumentFromStreamAndClose(report_xml.out_format.filter_name)
                        except Exception as e:
                            logger.error(str(e))
                            if retry>0:
                                logger.error("Failed to build subreport, retry %s" % retry)
                                time.sleep(AEROO_TIMEOUT)
                                return build_report(data,retry-1)

                            output=report_xml.in_format[3:]
                            raise e
                        finally:
                            self._cleanup_subreports()
                                    

                data = build_report(data)
            else:
                output=report_xml.in_format[3:]
        elif output in ('pdf', 'doc', 'xls'):
            output=report_xml.in_format[3:]
        #####################################
        return self._onResult(cr, uid, objects, (data, output), context=context)

    # override needed to keep the attachments' storing procedure
    def create_single_pdf(self, cr, uid, ids, data, report_xml, context=None):
        if report_xml.report_type == 'aeroo':
            if report_xml.out_format.code.startswith('oo-'):
                output = report_xml.out_format.code[3:]
                #print "uid:", uid, "ids:", ids, "data:", data, "report_xml:", report_xml, "context:", context, "output:", output
                #ids = [1364]
                return self.create_aeroo_report(cr, uid, ids, data, report_xml, context=context, output=output)
            elif report_xml.out_format.code =='genshi-raw':
                return self.create_genshi_raw_report(cr, uid, ids, data, report_xml, context=context, output='raw')
        
        logo = None        
        if context is None:
            context={}
        else:
            context = context.copy()
            
        title = report_xml.name
        rml = report_xml.report_rml_content
        oo_parser = self.parser(cr, uid, self.name2, context=context)
        objs = self.getObjects_mod(cr, uid, ids, report_xml, context, parser=oo_parser)
        oo_parser.set_context(objs, data, ids, report_xml.report_type)
        processed_rml = self.preprocess_rml(etree.XML(rml),report_xml.report_type)
        if report_xml.header:
            oo_parser._add_header(processed_rml)
        if oo_parser.logo:
            logo = base64.decodestring(oo_parser.logo)
        create_doc = self.generators[report_xml.report_type]
        pdf = create_doc(etree.tostring(processed_rml),oo_parser.localcontext,logo,title.encode('utf8'))
        return self._onResult(cr, uid, objects, (pdf, report_xml.report_type), context=context)

    def create_source_pdf(self, cr, uid, ids, data, report_xml, context=None):
        if not context:
            context={}
        pool = RegistryManager.get(cr.dbname)
        attachment_obj = pool.get('ir.attachment')
        attach = report_xml.attachment
        add_pdf_attachments = context.get("add_pdf_attachments",False)
        aeroo_ooo = self._aeroo_ooo_test(cr) # Detect report_aeroo_ooo module
        context['aeroo_ooo'] = aeroo_ooo
        if attach or add_pdf_attachments or aeroo_ooo and report_xml.process_sep:
            objs = self.getObjects(cr, uid, ids, context)
            results = []
            for obj in objs:
                aname = attach and eval(attach, {'object':obj, 'time':time}) or False
                attachment_id = None

                #create file name
                extension = report_xml.out_format.extension or "pdf"
                fname = aname
                if fname and not fname.endswith(extension):
                    fname = "%s.%s" % (fname,extension)

                result = False
                if report_xml.attachment_use and aname and context.get('attachment_use', True):
                    attachment_ids = attachment_obj.search(cr, uid, [('datas_fname','=',fname),('res_model','=',self.table),('res_id','=',obj.id)])
                    if attachment_ids:
                        attachment_id = attachment_ids[0]
                        attachment = attachment_obj.browse(cr, uid, attachment_id)
                        if attachment.datas:
                            d = base64.decodestring(attachment.datas)
                            result = self._onResult(cr, uid, [obj], (d,extension,attachment.name,attachment.datas_fname), context=context)
                        else:
                            logger.error("Attachment for %s - %s for reloading does not exists. Try to create a new one..." % (aname,fname))

                if not result:
                    # create report
                    result = self.create_single_pdf(cr, uid, [obj.id], data, report_xml, context)
                    if not result:
                        return False
                    # build result
                    result = (result[0],result[1],aname,fname)
                    try:
                        if attach and aname:
                            #create file name again
                            extension = result[1] or "pdf"
                            fname = aname
                            if not fname.endswith(extension):
                                fname = "%s.%s" % (fname,extension)
                            #create attachment
                            attachment_id = attachment_obj.create(cr, uid, {
                                'name': aname,
                                'datas': base64.encodestring(result[0]),
                                'datas_fname': fname,
                                'res_model': self.table,
                                'res_id': obj.id,
                                }) # no context to prevent wrong default values
                            cr.commit()
                    except Exception,e:
                         tb_s = reduce(lambda x, y: x+y, traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
                         logger.error(str(e))

                #add result
                results.append(result)

                # add pdf attachments
                if add_pdf_attachments:
                    attachment_ids =attachment_obj.search(cr, uid, [('id','!=',attachment_id),('res_model','=',self.table),('res_id','=',obj.id)])
                    for attachment in attachment_obj.browse(cr, uid, attachment_ids, context=context):
                        if attachment.datas and attachment.datas_fname and attachment.datas_fname.endswith(".pdf"):
                            d = base64.decodestring(attachment.datas)
                            results.append((d,"pdf",attachment.name,attachment.datas_fname))


            if results:
                if results[0][1]=='pdf':
                    output = PdfFileWriter()
                    for r in results:
                        reader = fixPdf(r[0],ret_reader=True)
                        if reader:
                            for page in range(reader.getNumPages()):
                                output.addPage(reader.getPage(page))
                        else:
                            logger.error("Unable to merge corrupted PDF %s - %s" % (r[2],r[3]))

                    s = StringIO()
                    output.write(s)
                    return s.getvalue(), results[0][1]
        return self.create_single_pdf(cr, uid, ids, data, report_xml, context)

    def create_source_odt(self, cr, uid, ids, data, report_xml, context=None):
        if not context:
            context={}
        pool = RegistryManager.get(cr.dbname)
        report_obj = pool.get("ir.actions.report.xml")
        results = []
        attach = report_xml.attachment
        aeroo_ooo = self._aeroo_ooo_test(cr) # Detect report_aeroo_ooo module
        context['aeroo_ooo'] = aeroo_ooo
        if attach or aeroo_ooo and report_xml.process_sep:
            oo_parser = self.parser(cr, uid, self.name2, context=context)
            objs = self.getObjects_mod(cr, uid, ids, report_xml, context, parser=oo_parser)
            for obj in objs:
                aname = attach and eval(attach, {'object':obj, 'time':time}) or False
                result = False
                if report_xml.attachment_use and aname and context.get('attachment_use', True):
                    aids = pool.get('ir.attachment').search(cr, uid, [('datas_fname','=',aname+'.odt'),('res_model','=',self.table),('res_id','=',obj.id)])
                    if aids:
                        brow_rec = pool.get('ir.attachment').browse(cr, uid, aids[0])
                        if not brow_rec.datas:
                            continue
                        d = base64.decodestring(brow_rec.datas)
                        results.append((d,'odt'))
                        continue
                result = self.create_single_pdf(cr, uid, [obj.id], data, report_xml, context)
                try:
                    if attach and aname:
                        name = aname+'.'+result[1]
                        pool.get('ir.attachment').create(cr, uid, {
                            'name': aname,
                            'datas': base64.encodestring(result[0]),
                            'datas_fname': name,
                            'res_model': self.table,
                            'res_id': obj.id,
                            }, context=context
                        )
                        cr.commit()
                except Exception,e:
                    logger.error(str(e))
                results.append(result)

        # build report
        if results and len(results)==1:
            return results[0]
        elif not results:
            return self.create_single_pdf(cr, uid, ids, data, report_xml, context)
        else:
            def build_report(retry=AEROO_RETRIES):
                try:
                    with report_obj._new_ooproxy(cr,uid,context=context) as DC:
                        if DC:
                            doc_list = list(reversed(results))
                            doc_data = doc_list.pop()
                            DC.putDocument(doc_data[0])
                            DC.joinDocuments([d[0] for d in doc_list])
                            doc = DC.readDocumentFromStreamAndClose()
                            return (doc, doc_data[1])
                        else:
                            return self.create_single_pdf(cr, uid, ids, data, report_xml, context)
                except Exception as e:
                    if retry > 0:
                        time.sleep(AEROO_TIMEOUT)
                        logger.error("Failed to build report, retry %s" % retry)
                        return build_report(data,retry-1)
                    raise e

            return build_report(retry)

    # override needed to intercept the call to the proper 'create' method
    def create(self, cr, uid, ids, data, context=None):
        pool = RegistryManager.get(cr.dbname)
        ir_obj = pool.get('ir.actions.report.xml')
        report_xml_ids = ir_obj.search(cr, uid,
                [('report_name', '=', self.name[7:])], context=context)
        if report_xml_ids:
            report_xml = ir_obj.browse(cr, uid, report_xml_ids[0], context=context)
        else:
            title = ''
            rml = tools.file_open(self.tmpl, subdir=None).read()
            report_type= data.get('report_type', 'pdf')
            class a(object):
                def __init__(self, *args, **argv):
                    for key,arg in argv.items():
                        setattr(self, key, arg)
            report_xml = a(title=title, report_type=report_type, report_rml_content=rml, name=title, attachment=False, header=self.header)

        report_type = report_xml.report_type
        if report_type in ['sxw','odt']:
            fnct = self.create_source_odt
        elif report_type in ['pdf','raw','txt','html']:
            fnct = self.create_source_pdf
        elif report_type=='html2html':
            fnct = self.create_source_html2html
        elif report_type=='mako2html':
            fnct = self.create_source_mako2html
        elif report_type=='aeroo':
            if report_xml.out_format.code in ['oo-pdf']:
                fnct = self.create_source_pdf
            elif report_xml.out_format.code in ['oo-odt','oo-ods','oo-doc','oo-xls','genshi-raw']:
                fnct = self.create_source_odt
            else:
                return super(Aeroo_report, self).create(cr, uid, ids, data, context)
        else:
            raise Exception('Unknown Report Type')
        return fnct(cr, uid, ids, data, report_xml, context)

class ReportTypeException(Exception):
    def __init__(self, value):
      self.parameter = value
    def __str__(self):
      return repr(self.parameter)

