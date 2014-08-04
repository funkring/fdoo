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

from openerp.modules.registry import RegistryManager
from openerp.osv.fields import float as float_class, function as function_class, datetime as datetime_field
from datetime import datetime
import time
import util
import math
import openerp.tools

class LangFormat(object):
    
    """ A simple lang format class """
    def __init__(self, cr, uid, context=None, dp=None, obj=None, f=None):
        if not context:
            context={}
            
        self.cr = cr
        self.uid = uid
        self.pool = RegistryManager.get(cr.dbname)
        self.lang = context.get("lang",None)
        self.user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        self.dp = dp
        self.obj = obj
        self.f = f
        
        if not self.lang:
            self.lang = self.user.company_id.partner_id.lang or openerp.tools.config.defaultLang

                        
    def _get_lang_dict(self):
        pool_lang = self.pool.get('res.lang')        
        lang_ids = pool_lang.search(self.cr,self.uid,[('code','=',self.lang)])[0]
        lang_obj = pool_lang.browse(self.cr,self.uid,lang_ids)
        return {'lang_obj':lang_obj,'date_format':lang_obj.date_format,'time_format':lang_obj.time_format}        


    def digits_fmt(self, obj=None, f=None, dp=None):
        digits = self.get_digits(obj, f, dp)
        return "%%.%df" % (digits, )

    
    def get_digits(self, obj=None, f=None, dp=None):
        d = DEFAULT_DIGITS = 2
        if dp:
            decimal_precision_obj = self.pool.get('decimal.precision')
            ids = decimal_precision_obj.search(self.cr, self.uid, [('name', '=', dp)])
            if ids:
                d = decimal_precision_obj.browse(self.cr, self.uid, ids)[0].digits
        elif obj and f:
            res_digits = getattr(obj._columns[f], 'digits', lambda x: ((16, DEFAULT_DIGITS)))
            if isinstance(res_digits, tuple):
                d = res_digits[1]
            else:
                d = res_digits(self.cr)[1]
        elif (hasattr(obj, '_field') and\
                isinstance(obj._field, (float_class, function_class)) and\
                obj._field.digits):
                d = obj._field.digits[1] or DEFAULT_DIGITS
        return d

    def digits(self):
        return self.get_digits(obj=self.obj, f=self.f, dp=self.dp)
    

    def floatTimeConvert(self,float_val):
        if not float_val:
            return "00:00"
        
        hours = math.floor(abs(float_val))
        mins = round(abs(float_val)%1+0.01,2)
        if mins >= 1.0:
            hours = hours + 1
            mins = 0.0
        else:
            mins = mins * 60
        float_time = '%02d:%02d' % (hours,mins)
        return float_time
    
    
    def formatLang(self, value, digits=None, date=False, date_time=False, grouping=True, monetary=False, dp=False,float_time=False):
        """
            Assuming 'Account' decimal.precision=3:
                formatLang(value) -> digits=2 (default)
                formatLang(value, digits=4) -> digits=4
                formatLang(value, dp='Account') -> digits=3
                formatLang(value, digits=5, dp='Account') -> digits=5
        """
        if digits is None:
            if not dp:
                dp  = self.dp            
            if dp:
                digits = self.get_digits(dp=dp)
            elif self.obj and self.f:
                digits = self.get_digits(obj=self.obj,f=self.f)
            elif value:
                digits = self.get_digits(value)
            else:
                digits = 2                

        if isinstance(value, (str, unicode)) and not value:
            return ''

        lang_dict = self._get_lang_dict()        
        if date or date_time:
            if not str(value):
                return ''

            date_format = lang_dict['date_format']
            parse_format = util.DT_FORMAT
            if date_time:                
                value=value.split('.')[0]
                date_format = date_format + " " + lang_dict['time_format']
                parse_format = util.DHM_FORMAT
            if not isinstance(value, time.struct_time):
                return time.strftime(date_format, time.strptime(value, parse_format))
            else:
                date = datetime(*value.timetuple()[:6])
            
            if date_time:
                # Convert datetime values to the expected client/context timezone
                date = datetime_field.context_timestamp(self.cr, self.uid,
                                                        timestamp=date,
                                                        context=self.localcontext)
                
            return date.strftime(date_format)
        elif float_time:
            return self.floatTimeConvert(value)

        return lang_dict['lang_obj'].format('%.' + str(digits) + 'f', value, grouping=grouping, monetary=monetary)