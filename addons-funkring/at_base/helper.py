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

import os
import util
import openerp
import pytz
import sys
import zipimport
import imp

from openerp import netsvc
from openerp.osv.fields import datetime as datetime_field
from openerp.tools.translate import _
from format import LangFormat
from openerp import SUPERUSER_ID
from openerp import tools
import base64

def getMonthNames(cr, uid, context=None):
    return [
      _("January"),
      _("February"),
      _("March"),
      _("April"),
      _("May"),
      _("June"),
      _("July"),
      _("August"),
      _("September"),
      _("October"),
      _("November"),
      _("December")
    ]
    
def getDayNames(cr, uid, context=None):
    return [
      (_("Monday"),   _("Mon")),
      (_("Tuesday"),  _("Tue")),
      (_("Wednesday"),_("Wed")),
      (_("Thursday"), _("Thu")),
      (_("Friday"),   _("Fri")),
      (_("Saturday"), _("Sat")),
      (_("Sunday"),   _("Sun")),
    ]

def getMonthName(cr, uid, month, context=None):
    return getMonthNames(cr, uid, context=context)[month-1]

def getRangeName(cr, uid, start_date, end_date, context):
    if not start_date or not end_date:
        return ""
    if start_date == end_date:
        f = LangFormat(cr, uid, context=context)
        return "%s, %s" % (f.formatLang(start_date, date=True), f.getDayShortName(start_date))
    else:
        start = util.strToDate(start_date)
        end = util.strToDate(end_date)
        if start.month==1 and end.month==3 and start.year == end.year:
            return _("1st Quarter %s") % (end.strftime("%Y"),)
        elif start.month==4 and end.month==6 and start.year == end.year:
            return _("2nd Quarter %s") % (end.strftime("%Y"),)
        elif start.month==7 and end.month==9 and start.year == end.year:
            return _("3rd Quarter %s") % (end.strftime("%Y"),)
        elif start.month==10 and end.month==12 and start.year == end.year:
            return _("4th Quarter %s") % (end.strftime("%Y"),)
        else:
            if util.getFirstOfMonth(start_date) == start_date and util.getEndOfMonth(end_date) == end_date:
                return getMonthYearRange(cr,uid,start_date,end_date,context)
            else:
                f = LangFormat(cr, uid, context=context)
                return "%s - %s" % (f.formatLang(start_date, date=True),f.formatLang(end_date, date=True))

def getMonth(cr, uid, str_date, context=None):
    d_date = util.strToDate(str_date)
    return getMonthName(cr, uid, d_date.month, context=context)

def getMonthYear(cr, uid, str_date, context=None):
    d_date = util.strToDate(str_date)
    str_pattern = getMonthName(cr, uid, d_date.month, context=context) + " %Y"
    return d_date.strftime(str_pattern)

def getMonthYearRange(cr, uid, str_from, str_to, context=None):
    if str_from and str_to:
        res_from = getMonthYear(cr,uid,str_from,context)
        res_to = getMonthYear(cr,uid,str_to,context)
        if res_from == res_to:
            return res_from
        return "%s - %s" % (res_from,res_to)
    elif str_from:
        return getMonthYear(cr,uid,str_from,context)
    elif str_to:
        return getMonthYear(cr,uid,str_to,context)
    return ""

def printReport(cr, uid, report,model, ids, printer=None, context=None):
    report_obj = netsvc.LocalService("report."+report)
    data, format = report_obj.create(cr, uid, ids, {"model" : model }, context)

    fd = None
    if printer:
        fd = os.popen("lp -d " + printer,"wb")
    else:
        fd = os.popen("lp","wb")

    if fd:
        fd.write(data)
        fd.close()
    return True


def printRaw(cr, uid, data, printer=None, context=None):
    fd = None
    if printer:
        fd = os.popen("lp -o raw -d " + printer,"wb")
    else:
        fd = os.popen("lp -o raw","wb")

    if fd:
        fd.write(data)
        fd.close()

    return True


def printText(cr, uid, data, printer=None, context=None):
    fd = None
    if printer:
        fd = os.popen("lp -d " + printer,"wb")
    else:
        fd = os.popen("lp","wb")

    if fd:
        fd.write(data)
        fd.close()

    return True


def strToLocalTimeStr(cr, uid, str_time, context):
    # Convert datetime values to the expected client/context timezone
    timestamp=util.strToTime(str_time)
    converted = datetime_field.context_timestamp(cr, uid,
                                            timestamp=timestamp,
                                            context=context)
    return util.timeToStr(converted)

def strToLocalDateStr(cr, uid, str_time, context):
    # Convert datetime values to the expected client/context timezone
    timestamp=util.strToTime(str_time)
    converted = datetime_field.context_timestamp(cr, uid,
                                            timestamp=timestamp,
                                            context=context)
    return util.timeToDateStr(converted)

def strToLocalTimeFormat(cr, uid, str_time, format, context):
    # Convert datetime values to the expected client/context timezone
    timestamp=util.strToTime(str_time)
    converted = datetime_field.context_timestamp(cr, uid,
                                            timestamp=timestamp,
                                            context=context)
    return util.dateFormat(converted, format)

def strDateToUTCTimeStr(cr, uid, str_date, context):
    timestamp=util.strToTime(util.dateToTimeStr(str_date))
    converted = datetime_field.context_timestamp(cr, uid,
                                            timestamp=timestamp,
                                            context=context)
    converted = util.strToTime(util.timeToStr(converted))
    diff = (converted-timestamp)
    utcTimestamp = timestamp - diff
    return util.timeToStr(utcTimestamp)


def strTimeToUTCTimeStr(cr, uid, timestamp, context):
    context_tz = context and context.get('tz') or None
    tz_name = None
    if context_tz:
        tz_name = context_tz
    else:
        registry = openerp.modules.registry.RegistryManager.get(cr.dbname)
        user = registry['res.users'].browse(cr, SUPERUSER_ID, uid)
        tz_name = user.tz
        
    if not tz_name:
        return timestamp
    
    tz = pytz.timezone(tz_name)
    l_timestamp = tz.localize(util.strToTime(timestamp))
    l_timestamp = l_timestamp.astimezone(pytz.utc)
    return util.timeToStr(l_timestamp)
  
  
def onChangeValuesEnv(line_obj, values, onchange_values, force=False):
    if onchange_values:
      update_values = onchange_values.get("value")
      if update_values:
        fields = update_values.keys()
        field_defs = line_obj.fields_get(allfields=fields)        
        for field, update_value in update_values.iteritems():
          if not force and not update_value:
            continue
          if field_defs[field]["type"] == "many2many":
            values[field] = [(6,0, update_value or [])]
          else:
            values[field] = update_value
    return values
      
def onChangeValuesPool(cr, uid, line_obj, values, onchange_values, force=False, context=None):
    if onchange_values:
      update_values = onchange_values.get("value")
      if update_values:
        fields = update_values.keys()
        field_defs = line_obj.fields_get(cr, uid, allfields=fields, context=context)        
        for field, update_value in update_values.iteritems():
          if not force and not update_value:
            continue
          if field_defs[field]["type"] == "many2many":
            values[field] = [(6,0, update_value or [])]
          else:
            values[field] = update_value
    return values
  
def renderReportEnv(obj, report_name, encode=False):
    cr = obj._cr
    uid = obj._uid
    report_context = dict(obj._context)
    report_obj = obj.env.registry["ir.actions.report.xml"]
    report = report_obj._lookup_report(cr, report_name)
    if report:
      values = {}      
      (report_data, report_ext) = report.create(cr, uid, obj.ids, values, context=report_context)
      if len(obj.ids) > 1:
        name_first = obj[0].name_get()[0][1]
        name_last = obj[-1].name_get()[0][1]
        name = "%s-%s.%s" % (util.cleanFileName(name_first), util.cleanFileName(name_last), report_ext)        
      else:
        name_first = obj.name_get()[0][1]
        name = "%s.%s" % (util.cleanFileName(name_first), report_ext)
      if encode:
        report_data = report_data and base64.encodestring(report_data) or None
      return (report_data, report_ext, name)
    return (None, None, None)
  
def downloadTestReportEnv(objects, report_name, file_name=None):
    test_download = tools.config.get("test_download")
    res = []
    if test_download:
      for obj in objects:
        (report_data, report_ext, report_file) = renderReportEnv(obj, report_name)
      if file_name:
        report_file = file_name
      if report_data:
        download_path = os.path.join(test_download, report_file)
        with open(download_path, "wb") as f:
          f.write(report_data)
        res.append(download_path)
    return res
  
def downloadTestAttachmentEnv(obj):
    test_download = tools.config.get("test_download")
    res = []
    if test_download:
      att_obj = obj.env["ir.attachment"]
      for att in att_obj.search([("res_model","=", obj._model._name), ("res_id","=", obj.id)]):
        download_path = os.path.join(test_download, att.datas_fname)
        with open(download_path, "wb") as f:
          f.write(base64.decodestring(att.datas))
        res.append(download_path)
    return res

def getResource(path):
    ad = os.path.abspath(os.path.join(tools.ustr(tools.config["root_path"]), u"addons"))
    mod_path_list = map(lambda m: os.path.abspath(tools.ustr(m.strip())), tools.config["addons_path"].split(','))
    mod_path_list.append(ad)
    for mod_path in mod_path_list:
      module_path = mod_path+os.path.sep+path.split(os.path.sep)[0]
      
      if os.path.lexists(module_path):
        filepath = mod_path+os.path.sep+path
        filepath = os.path.normpath(filepath)
        
        python_path = os.path.dirname(filepath)
        if not python_path in sys.path:
          sys.path.append(python_path)
                   
        return {
          "module": module_path,
          "path": filepath,
          "zip": False
        }
                
      else:
        zip_path = module_path+'.zip'
        if os.path.lexists(zip_path):
          return {
            "module": path.split(os.path.sep)[0],
            "path": zip_path,
            "zip": True
          }
        
def loadClassFromFile(env, path, clazz, key="1"):
    res = getResource(path)
    if not res:
      return None
    
    if res.get("zip"):
      zimp = zipimport.zipimporter(res["path"])
      return getattr(zimp.load_module(res["module"]).parser, clazz)
    
    else:
      dbname = env.cr.dbname
      filepath = res["path"]
      
      mod_name, file_ext = os.path.splitext(os.path.split(res["path"])[-1])
      mod_name = '%s_%s_%s' % (dbname, mod_name, key)
      
      if file_ext.lower() == '.py':
        py_mod = imp.load_source(mod_name, filepath)
  
      elif file_ext.lower() == '.pyc':
          py_mod = imp.load_compiled(mod_name, filepath)
  
      if clazz in dir(py_mod):
        return getattr(py_mod, clazz)
      
    return None
        
