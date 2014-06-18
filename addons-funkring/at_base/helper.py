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

from openerp import netsvc
import os
import util
from openerp.osv.fields import datetime as datetime_field
from openerp.tools.translate import _
from format import LangFormat

def getMonthName(cr,uid,month,context=None):
    month_names = [
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
    return month_names[month-1]

def getRangeName(cr,uid,start_date,end_date,context):        
    if not start_date or not end_date:
        return ""    
    if start_date == end_date:
        f = LangFormat(cr, uid, context=context)
        return f.formatLang(start_date, date=True)
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
    

def getMonth(cr,uid,str_date,context=None):    
    d_date = util.strToDate(str_date)
    return getMonthName(cr,uid,d_date.month)

def getMonthYear(cr,uid,str_date,context=None):    
    d_date = util.strToDate(str_date)
    str_pattern = getMonthName(cr,uid,d_date.month) + " %Y"
    return d_date.strftime(str_pattern)

def getMonthYearRange(cr,uid,str_from,str_to,context=None):
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

def printReport(cr,uid,report,model,ids,printer=None,context=None):
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
    
    
def printRaw(cr,uid,data,printer=None,context=None):
    fd = None
    if printer:
        fd = os.popen("lp -o raw -d " + printer,"wb")
    else:
        fd = os.popen("lp -o raw","wb")    
        
    if fd:
        fd.write(data)
        fd.close()
    
    return True


def printText(cr,uid,data,printer=None,context=None):
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


def sendMails(pool, cr, uid, template_xmlid, res_ids, context=None):
    """
    send mails from template with passed xmlid for passed resources
    """
    template_obj = pool.get("email.template")
    template_id = pool.get("ir.model").xmlid_to_res_id(cr, uid, "academy.email_template_registration")
    if template_id: 
        for oid in ids:
            template_obj.send_mail(cr, uid, template_id, res_id, context=context)
