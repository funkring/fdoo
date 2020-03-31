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

import time
import pytz

from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import date

from openerp import models, fields, api, _


DT_FORMAT = "%Y-%m-%d"
DHM_FORMAT = "%Y-%m-%d %H:%M:%S"
HM_FORMAT = "%H:%M:%S"
HM_FORMAT_SHORT = "%H:%M"

ISO_FORMAT_UTC = "%Y-%m-%dT%H:%M:%SZ"


class UtilTime(models.AbstractModel):
    _name = "util.time"

    def _strToTime(self, time_str):
        if not time_str:
            return time_str
        if isinstance(time_str, datetime):
            return time_str
        pos = time_str.find(".")
        if pos > 0:
            time_str = time_str[:pos]
        return datetime.strptime(time_str, DHM_FORMAT)

    def _timeToStr(self, time_dt):
        return datetime.strftime(time_dt, DHM_FORMAT)

    def _strToDate(self, date_str):
        if not date_str:
            return date_str
        if isinstance(date_str, datetime):
            return date_str
        if len(date_str) > 10:
            date_str = self._timeToDateStr(date_str)
        return datetime.strptime(date_str, DT_FORMAT)

    def _dateToStr(self, date_dt):
        return datetime.strftime(date_dt, DT_FORMAT)
    
    def _dateToTimeStr(self, date_str):        
        if len(date_str) <= 10:
            return "%s 00:00:00" % date_str
        return date_str

    def _formatDate(self, date_str, format_str):
        dt = self._strToDate(date_str)
        return datetime.strftime(dt, format_str)
    
    def _toDateTimeUser(self, time_str):
        user_tz = pytz.timezone(self.env.user.tz or pytz.utc)
        return datetime.strftime(pytz.utc.localize(datetime.strptime(time_str,
            DHM_FORMAT)).astimezone(user_tz),DHM_FORMAT)
   
    def _toDateUser(self, time_str):
        time_str = self._dateToStr(time_str)
        user_tz = pytz.timezone(self.env.user.tz or pytz.utc)
        return datetime.strftime(pytz.utc.localize(datetime.strptime(time_str,
            DHM_FORMAT)).astimezone(user_tz),DT_FORMAT)
        
    def _toDateTimeUTC(self, time_str):
        user_tz = pytz.timezone(self.env.user.tz or pytz.utc)
        return datetime.strftime(user_tz.localize(datetime.strptime(time_str,
            DHM_FORMAT)).astimezone(pytz.utc),DHM_FORMAT)
        
    def _toDateUserUTC(self, time_str):
        time_str = self._dateToStr(time_str)
        user_tz = pytz.timezone(self.env.user.tz or pytz.utc)
        return datetime.strftime(user_tz.localize(datetime.strptime(time_str,
            DHM_FORMAT)).astimezone(pytz.utc),DT_FORMAT)
    
    def _currentDate(self):
        return time.strftime(DT_FORMAT)
    
    def _currentDateUTC(self):
        return datetime.utcnow().strftime(DT_FORMAT)
    
    def _currentDateTime(self):
        return time.strftime(DHM_FORMAT)
    
    def _currentDateTimeUTC(self):
        return datetime.utcnow().strftime(DHM_FORMAT)
    
    def _firstOfMonth(self, date_str):
        if not date_str:
            return date_str
        date_dt = self._strToDate(date_str)
        return self._dateToStr(date(date_dt.year, date_dt.month, 1))
    
    def _lastMonth(self, date_str):
        if not date_str:
            return date_str
        date_dt = self._strToDate(date_str)
        date_dt -= relativedelta(months=1)
        return self._dateToStr(date_dt)

    def _firstOfLastMonth(self):
        return self._firstOfMonth(self._lastMonth(self._currentDate()))
