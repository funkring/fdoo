# -*- coding: utf-8 -*-
"""
Barcodes for Python, GS1 package
Copyright 2009  Peter Gebauer

This module provides simplified GS1-type barcodes. They are basically Code-128
barcodes with specifications for the contents and their 'applications'.

Because of how Gs1 barcodes are printed parenthesis are NOT allowed as
symbols. They are only to be used in Gs1.from_unicode to denote application
identifiers.

NOTE: I've only implemented the applications I'm going to use, these
include 00, 01, 02, 10, 11, 12, 13, 15, 17 and 30. All are related to shipping
provisions, it should be easy enough to add new assertions for applications.
You can always add unknown applications at will if assertions are not required.


"Barcodes for Python" is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

"Barcodes for Python" is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
(see file COPYING) along with "Barcodes for Python".
If not, see <http://www.gnu.org/licenses/>.
"""
from datetime import date, datetime
from decimal import Decimal
import time

from . import Barcode, group_string
import code128
import ean


class AssertApp(object):

    def __init__(self, type_, min_ = 0, max_ = None):
        self.type = type_
        if type_ == date:
            self.min = 6
            self.max = 6
        else:
            self.min = min_
            self.max = max_

    def assert_ascii(self, value):
        try:
            return value.encode("ascii")
        except UnicodeEncodeError:
            raise AssertionError("invalid ascii")

    def assert_length(self, value):
        value = self.assert_ascii(value)
        assert len(value) >= self.min and (self.max is None or len(value) <= self.max), "invalid length"
        return value

    def assert_integer(self, value):
        value = self.assert_length(value)
        try:
            return int(value)
        except (ValueError, TypeError):
            raise AssertionError("invalid integer")

    def assert_decimal(self, value):
        value = self.assert_length(value)
        try:
            return Decimal("%s"%value)
        except (ValueError, TypeError):
            raise AssertionError("invalid decimal '%s'"%value)

    def assert_date(self, value):
        value = self.assert_length(value)
        try:
            return datetime.strptime("%s"%value, "%y%m%d")
        except (ValueError, TypeError):
            raise AssertionError("invalid date")

    def assert_(self, value):
        if self.type == str:
            return self.assert_length(value)
        elif self.type == int:
            return self.assert_integer(value)
        elif self.type == Decimal:
            return self.assert_decimal(value)
        elif self.type == date:
            return self.assert_date(value)
        

APPLICATION_ASSERTIONS = {
    "00": AssertApp(str, 18),
    "01": AssertApp(str, 14),
    "02": AssertApp(str, 14),
    "10": AssertApp(str, 0, 20),
    "11": AssertApp(date),
    "12": AssertApp(date),
    "13": AssertApp(date),
    "15": AssertApp(date),
    "17": AssertApp(date),
    "30": AssertApp(int, 0, 8),
    }


def gs1_unicode_to_applications(u):
    """
    Converts the application formatted unicode string as a list
    of id/value tuples.
    """
    ret = []
    count = 0
    while u and count < 0xff:
        index1 = u.find("(")
        if index1 < 0:
            raise ValueError("application start paranthesis missing at '%s'"%u)
        index2 = u.find(")")
        if index2 < 0 or index2 < index1:
            raise ValueError("application end paranthesis missing or invalid at '%s'"%u)
        id_ = u[index1 + 1:index2]
        u = u[index2 + 1:]
        next_start = u.find("(")
        if next_start < 0:
            value = u
        else:
            value = u[:next_start]
        if id_ in APPLICATION_ASSERTIONS:
            try:
                value = APPLICATION_ASSERTIONS[id_].assert_(value)
            except AssertionError, ae:
                raise AssertionError("error in application '%s', %s"%(id_, ae))
            ret.append(("%s"%id_, value))
            if next_start >= 0:
                u = u[next_start:]
            else:
                u = ""
        else:
            raise NotImplementedError("application '%s' not implemented"%id_)
        count += 1
    return ret


def gs1_applications_to_unicode(applications):
    """
    Returns a unicode from a list of application tuples.
    """
    ret = []
    for id_, value in applications:
        if id_ in APPLICATION_ASSERTIONS:
            if hasattr(value, "strftime"):
                value = date.strftime(value, "%y%m%d")
            try:
                APPLICATION_ASSERTIONS[id_].assert_("%s"%value)
            except AssertionError, ae:
                raise AssertionError("error in application '%s', %s"%(id_, ae))
            ret.append(u"(%s)%s"%(id_, value))
        else:
            raise NotImplementedError("application '%s' not implemented"%id_)
    return u"".join(ret)


def gs1_applications_to_symbols(applications, terminator = "FNC1"):
    """
    Converts a list of application tuples into Code128 symbols.
    Variable length application values are terminated with FNC1.
    Optional second argument can be used to change the terminator code,
    the Code128 string aliases are used (i.e 'FNC1', 'STOP', etc).
    """
    ret = ["START_B"]
    for id_, value in applications:
        if id_ in APPLICATION_ASSERTIONS:
            if hasattr(value, "strftime"):
                value = date.strftime(value, "%y%m%d")
            else:
                value = "%s"%value
            try:
                APPLICATION_ASSERTIONS[id_].assert_("%s"%value)
            except AssertionError, ae:
                raise AssertionError("error in application '%s', %s"%(id_, ae))
            ret += list(id_)
            ret += list(value)
            if APPLICATION_ASSERTIONS[id_].min != APPLICATION_ASSERTIONS[id_].max and len(value) < APPLICATION_ASSERTIONS[id_].max:
                ret.append("FNC1")
        else:
            raise NotImplementedError("application '%s' not implemented"%id_)
    ret.append("STOP")
    return code128.code128_strings_to_symbols(ret)


def gs1_symbols_to_applications(symbol_list, terminator = "FNC1"):
    """
    Converts symbols to a list of application tuples. Optional terminator
    argument can be changed from 'FNC1' to what you use as terminator
    of variable length application values.
    """
    strings = code128.code128_symbols_to_strings(symbol_list)
    current = u""
    for s in strings:
        if len(s) == 1:
            current += u"%s"%s
        elif s == "FNC1":
            current += u"\256"
    count = 0
    ret = []
    while current and count < 0xff:
        id_ = current[:2]
        if id_ in APPLICATION_ASSERTIONS:
            current = current[2:]
            app = APPLICATION_ASSERTIONS[id_]
            if app.max == app.min or app.max == None:
                value = current[:app.min]
                current = current[app.min:]
            else:
                index = current.find(u"\256")
                if index >= 0:
                    value = current[:index]
                    current = current[index + 1:]
                else:
                    value = current[:app.max]
                    current = current[app.max:]
            try:
                ret.append((id_, app.assert_("%s"%value)))
            except AssertionError, ae:
                raise AssertionError("error in application '%s', %s"%(id_, ae))
        else:
            raise NotImplementedError("application '%s' not implemented"%id_)
        count += 1
    return ret
            

class Gs1(code128.Code128):
    """
    Same as Code128, but with some added methods for handling applications.
    """

    @staticmethod
    def from_unicode(u):
        applications = gs1_unicode_to_applications(u)
        symstrings = list("".join([id_ + value for id_, value in applications]))
        return Gs1.from_strings(["START_B"] + symstrings + ["STOP"])

    def to_unicode(self):
        ret = []
        for id_, value in gs1_symbols_to_applications(self.get_symbols()):
            ret.append(u"(%s)%s"%(id_, value))
        return u"".join(ret)

    def get_name(self):
        return "Gs1-128"

    def get_applications(self):
        return gs1_symbols_to_applications(self.get_symbols())

    def set_applications(self, applications):
        self.set_symbols(gs1_applications_to_symbols(applications))

    def get_application(self, id_):
        apps = self.get_applications()
        for id2, value in apps:
            if id2 == id_:
                return value
        return None

    def set_application(self, id_, value):
        if not id_ in APPLICATION_ASSERTIONS:
            raise NotImplementedError("application '%s' not implemented"%id_)
        if hasattr(value, "strftime"):
            value = date.strftime(value, "%y%m%d")
        else:
            value = "%s"%value
        value = APPLICATION_ASSERTIONS[id_].assert_(value)
        newapps = []
        apps = self.get_applications()
        for id2, value2 in apps:
            if id2 == id_:
                newapps.append((id_, value))
            else:
                newapps.append((id2, value2))
        self.set_applications(newapps)

    def remove_application(self, id_):
        if not id_ in APPLICATION_ASSERTIONS:
            raise NotImplementedError("application '%s' not implemented"%id_)
        if hasattr(value, "strftime"):
            value = date.strftime(value, "%y%m%d")
        else:
            value = "%s"%value
        value = APPLICATION_ASSERTIONS[id_].assert_(value)
        newapps = []
        apps = self.get_applications()
        for id2, value2 in apps:
            if id2 != id_:
                newapps.append((id2, value2))
        self.set_applications(newapps)

    def to_unicode(self):
        return gs1_applications_to_unicode(self.get_applications())

    @classmethod
    def from_unicode(cls, u):
        return cls(gs1_applications_to_symbols(gs1_unicode_to_applications(u)))

    def set_from_unicode(self, u):
        self.set_symbols(gs1_applications_to_symbols(gs1_unicode_to_applications(u)))

    @classmethod
    def from_applications(cls, apps):
        return cls(gs1_applications_to_symbols(apps))
    
