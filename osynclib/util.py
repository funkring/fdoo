# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime
import logging

_logger = logging.getLogger(__name__)
 
def init_logging():
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)
       
def get_encodings(hint_encoding='utf-8'):
    fallbacks = {
        'latin1': 'latin9',
        'iso-8859-1': 'iso8859-15',
        'cp1252': '1252',
    }
    if hint_encoding:
        yield hint_encoding
        if hint_encoding.lower() in fallbacks:
            yield fallbacks[hint_encoding.lower()]

    # some defaults (also taking care of pure ASCII)
    for charset in ['utf8','latin1']:
        if not hint_encoding or (charset.lower() != hint_encoding.lower()):
            yield charset

    from locale import getpreferredencoding
    prefenc = getpreferredencoding()
    if prefenc and prefenc.lower() != 'utf-8':
        yield prefenc
        prefenc = fallbacks.get(prefenc.lower())
        if prefenc:
            yield prefenc
        
            
def ustr(value, hint_encoding='utf-8', errors='strict'):
    """This method is similar to the builtin `unicode`, except
    that it may try multiple encodings to find one that works
    for decoding `value`, and defaults to 'utf-8' first.

    :param: value: the value to convert
    :param: hint_encoding: an optional encoding that was detecte
        upstream and should be tried first to decode ``value``.
    :param str errors: optional `errors` flag to pass to the unicode
        built-in to indicate how illegal character values should be
        treated when converting a string: 'strict', 'ignore' or 'replace'
        (see ``unicode()`` constructor).
        Passing anything other than 'strict' means that the first
        encoding tried will be used, even if it's not the correct
        one to use, so be careful! Ignored if value is not a string/unicode.
    :raise: UnicodeError if value cannot be coerced to unicode
    :return: unicode string representing the given value
    """
    if not value:
        return None
    
    if isinstance(value, unicode):
        return value

    if not isinstance(value, basestring):
        try:
            return unicode(value)
        except Exception:
            raise UnicodeError('unable to convert %r' % (value,))

    for ln in get_encodings(hint_encoding):
        try:
            return unicode(value, ln, errors=errors)
        except Exception:
            pass
    raise UnicodeError('unable to convert %r' % (value,)) 


def add_line(lines, value, label=None):
    if value:
        if label:
            lines.append("%s%s" % (label,value))
        else:
            lines.append(str(value))


class SqlConvert(object):

    def __init__(self,cr):
        '''
        Constructor
        '''
        self._cols = {}
        i=0
        descr = cr.description
        for field in descr:
            self._cols[field[0]]=i
            i+=1 
    
    def value_at(self,row,col):
        col_index = self._cols.get(col,None)
        if col_index is None:
            _logger.warn("column %s not found" % (col,))
        value = row[col_index]
        return value
            
    def ustr(self,row,col):
        return ustr(self.value_at(row, col))
    
    def float(self,row,col):
        value = self.value_at(row, col)
        if value:
            if isinstance(value,basestring):
                return float(str(value).replace(',', '.'))
            return float(value)        
        return None
    
    def int(self,row,col):
        value = self.value_at(row, col)
        if value:
            return int(value)        
        return None
    
    def date_str(self,row,col):
        value = self.value_at(row, col)
        if value:
            if type(value) in (datetime.date,datetime.datetime):
                return value.strftime("%Y-%m-%d")
            elif not isinstance(value,basestring) or len(value) != 10:
                _logger.warn("Unable to convert %s to date_str" % (str(value),))
        return value
    
    def datetime_str(self,row,col):
        value = self.value_at(row, col)
        if value:
            value_type = type(value)                        
            if value_type == datetime.datetime:
                return value.strftime("%Y-%m-%d %H:%M:%S")
            if value_type == datetime.date:
                return value.strftime("%Y-%m-%d 00:00:00")
            elif not isinstance(value,basestring) or len(value) != 19:
                _logger.warn("Unable to convert %s to datetime_str" % (str(value),))
        return value
    
    def time_str(self,row,col):
        value = self.value_at(row, col)
        if value:
            value_type = type(value)                        
            if value_type in (datetime.datetime,datetime.time):
                return value.strftime("%H:%M:%S")
            if value_type == datetime.date:
                return value.strftime("00:00:00")
            elif not isinstance(value,basestring) or len(value) != 8:
                _logger.warn("Unable to convert %s to time_str" % (str(value),))
        return value
    
    def time_value(self,row,col):
        value = self.value_at(row, col)
        if value:                        
            if type(value) in (datetime.time,datetime.datetime):
                value = float(value.hours)+(value.minute/60.0)+(value.second/3600.0)      
            else:
                _logger.warn("Unable to convert %s to time_value" % (str(value),))          
        return value
    
    def datetime_merge_str(self,row,col_date,col_time):
        value_date = self.date_str(row, col_date)
        value_time = self.time_str(row, col_time)
        if value_date:
            if value_time:
                return value_date + " " + value_time
            else:
                return value_date + " 00:00:00"
        return None
    
  
class SqlResultSet(object):                
    def __init__(self, con, rows):
        self.con = con
        self.row_it = rows and rows.__iter__() or None
        self.row = None
    
    def next(self):
        if self.row_it:
            try:
                self.row = self.row_it.next()
                if self.row:
                    return True            
            except StopIteration:
                pass
            
        self.row_it = None
        return False
    
    def value_at(self, col):
        return self.con.value_at(self.row,col)
            
    def ustr(self, col):
        return self.con.ustr(self.row,col)
    
    def float(self, col):
        return self.con.float(self.row,col)
          
    def int(self, col):
        return self.con.int(self.row,col)
    
    def date_str(self, col):
        return self.con.date_str(self.row,col)
    
    def datetime_str(self, col):
        return self.con.datetime_str(self.row,col)
    
    def time_str(self, col):
        return self.con.time_str(self.row,col)
    
    def time_value(self, col):
        return self.con.time_value(self.row,col)
    
    def datetime_merge_str(self, col_date, col_time):
        return self.con.datetime_merge_str(self.row, col_date, col_time)
