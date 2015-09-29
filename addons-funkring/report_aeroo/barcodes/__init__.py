# -*- coding: utf-8 -*-
"""
Barcodes for Python
Copyright 2009  Peter Gebauer

Python library for encoding and decoding numbers and text to and from
binary barcode representation strings.

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


def group_string(s, n, include_trailing = False):
    """
    Returns a list where the string elements are grouped by n-count.
    If the optional argument is True the last trailing portion of the
    string that didn't fit the n-count will be included at the end.
    """
    l = ["".join(c) for c in zip(*[list(s[i::n]) for i in range(n)])]
    if include_trailing:
        moddu = len(s) % n
        if moddu != 0:
            l.append("".join(s[-moddu:]))
    return l


class InvalidSymbolException(Exception):
    """
    Raised if a barcode is trying to use an invalid symbol.
    """

    def __init__(self, barcode_type, symbol, message = None):
        if not message:
            message = "'%s' is invalid symbol for %s"%(symbol, barcode_type.__name__)
        Exception.__init__(self, message)
        self.symbol = symbol
        self.barcode_type = barcode_type


class InvalidStringException(Exception):
    """
    Raised if the string cannot be translated into a proper list of symbols.
    """

    def __init__(self, barcode_type, problem):
        Exception.__init__(self, "invalid string for %s; %s"%(barcode_type.__name__, problem))


class DecodeException(Exception):
    """
    Raised when decoding a barcode string fails.
    """
    

class EncodeException(Exception):
    """
    Raised when encoding a symbol list fails.
    """
    

class Barcode(object):
    """
    Default, abstract barcode type.
    """

    def __init__(self, symbol_list):
        """
        A list argument containing symbols. A symbol is an integer
        describing a code point in a chart.
        """
        self.set_symbols(symbol_list)

    def set_symbols(self, symbol_list):
        """
        Set the symbol list.
        Will assert validity of the symbols or raise InvalidSymbolException.
        """
        self._symbols = symbol_list

    def get_symbols(self):
        """
        Return the list of symbols.
        """
        return self._symbols

    def encode(self):
        """
        Returns a string containing zero and non-zero. Each character is
        considered one bar.
        """
        raise NotImplementedError()

    @classmethod
    def decode(cls, s):
        """
        This will set the barcode using a string of bar digits.
        """
        raise NotImplementedError()

    def to_unicode(self):
        """
        Returns a human readable unicode string.
        Example for common use: zero is white and non-zero is black.
        """
        raise NotImplementedError()

    def set_from_unicode(self, u):
        """
        Update barcode symbols from unicode string.
        """
        raise NotImplementedError()

    @classmethod
    def from_unicode(cls, u):
        """
        Returns the barcode instance based on a human readable unicode string.
        Do not confuse this with the __str__ string.
        """
        raise NotImplementedError()

    def get_bar_geometries(self):
        """
        Return the barcode rectangles to be drawn along with their integer bar
        value. Each rectangle in the list is defined by a tuple containing left,
        top, width, height and the boolean bar value representing ON and OFF.
        All geometry values are floats describing their position in the barcode
        area wher 0.0 is left/top and 1.0 is right/bottom.
        """
        raise NotImplementedError()
        
    def get_unicode_geometries(self):
        """
        Return the symbol rectangles to be drawn along with their unicode glyph.
        Each rectangle in the list is defined by a tuple containing left,
        top, width, height and symbol value (unicode).
        All geometry values are floats describing their position in the barcode
        area wher 0.0 is left/top and 1.0 is right/bottom.
        """
        raise NotImplementedError()

    def get_name(self):
        """
        Returns the full name of the barcode standard.
        """
        raise NotImplementedError()

    def __repr__(self):
        return "<%s \"%s\">"%(self.get_name(), self.to_unicode())
    
