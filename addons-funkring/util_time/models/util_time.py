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

from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import date

from openerp import models, fields, api, _


DT_FORMAT = '%Y-%m-%d'
DHM_FORMAT = '%Y-%m-%d %H:%M:%S'
HM_FORMAT = '%H:%M:%S'
HM_FORMAT_SHORT = '%H:%M'

ISO_FORMAT_UTC = '%Y-%m-%dT%H:%M:%SZ'


class UtilTime(models.AbstractModel):
  _name = "util.time"

  def _strToTime(self, time_str):
    if not time_str:
        return time_str
    if isinstance(time_str,datetime):
        return time_str
    pos = time_str.find(".")
    if pos > 0:
      inTime = time_str[:pos]
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
  
  def _formatDate(self, date_str, format_str):
    dt = self._strToDate(date_str)
    return datetime.strftime(dt, format_str)
  