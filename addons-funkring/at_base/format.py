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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import time
import util
import math
import openerp.tools

def get_date_length(date_format=DEFAULT_SERVER_DATE_FORMAT):
    return len((datetime.now()).strftime(date_format))

class LangFormat(object):
    
    """ A simple lang format class """
    def __init__(self, cr, uid, context=None, dp=None, obj=None, f=None, dt=None, tz=None):
        if not context:
            context={}
            
        self.cr = cr
        self.uid = uid
        self.pool = RegistryManager.get(cr.dbname)
        self.lang = context.get("lang",None)
        self.user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        self.dp = dp
        self.dt = dt
        self.tz = context.get("tz") or tz
        self.obj = obj
        self.f = f
        self.evalContext = None
        
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

    def _check_digits(self, val):
        if val == 0:
            return val
        return val[1]
    
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
                res_digits = res_digits(self.cr)
                if res_digits == 0: # special digits, no rounding
                    d = res_digits
                else:
                    d = res_digits[1]
        elif (hasattr(obj, '_field') and\
                isinstance(obj._field, (float_class, function_class)) and\
                obj._field.digits):
                
                res_digits = obj._field.digits
                if res_digits == 0:  # special digits, no rounding
                    d = res_digits
                else:
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
    
    def evalStr(self, value):
        if self.evalContext is None:
            t = self.dt and util.strToTime(self.dt) or datetime.now()
            t = datetime_field.context_timestamp(self.cr, self.uid,
                                                        timestamp=t,
                                                        context={"tz":self.tz})
            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }
            self.evalContext = {key: t.strftime(sequence) for key, sequence in sequences.iteritems()}
        
        if value:
            return value % self.evalContext

        return value
    
    def formatLang(self, value, digits=None, date=False, date_time=False, grouping=True, monetary=False, dp=False, float_time=False):
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
            if not value:
                return ''

            date_format = lang_dict['date_format']
            parse_format = DEFAULT_SERVER_DATE_FORMAT
            if date_time:
                value = value.split('.')[0]
                date_format = date_format + " " + lang_dict['time_format']
                parse_format = DEFAULT_SERVER_DATETIME_FORMAT
            if isinstance(value, basestring):
                # FIXME: the trimming is probably unreliable if format includes day/month names
                #        and those would need to be translated anyway.
                date = datetime.strptime(value[:get_date_length(parse_format)], parse_format)
            elif isinstance(value, time.struct_time):
                date = datetime(*value[:6])
            else:
                date = datetime(*value.timetuple()[:6])
            if date_time:
                # Convert datetime values to the expected client/context timezone
                date = datetime_field.context_timestamp(self.cr, self.uid,
                                                        timestamp=date,
                                                        context={"tz":self.tz})
            return date.strftime(date_format.encode('utf-8'))
        elif float_time:
            return self.floatTimeConvert(value)
      
        if digits == 0:
            lang_dict['lang_obj'].format('%f', value, grouping=grouping, monetary=monetary)
        
        return lang_dict['lang_obj'].format('%.' + str(digits) + 'f', value, grouping=grouping, monetary=monetary)
    