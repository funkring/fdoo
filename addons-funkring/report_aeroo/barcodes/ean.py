# -*- coding: utf-8 -*-
"""
Barcodes for Python, EAN package
Copyright 2009  Peter Gebauer

EAN implementation of barcodes. Currently, only EAN-13 is supported.

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

from . import *

# These are the groups used for encoding.
ENCODING_L = ("0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011")
ENCODING_G = ("0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111")
ENCODING_R = ("1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100")

ENCODING_GROUPS = ((ENCODING_L,) * 6,
                   (ENCODING_L, ENCODING_L, ENCODING_G, ENCODING_L, ENCODING_G, ENCODING_G),
                   (ENCODING_L, ENCODING_L, ENCODING_G, ENCODING_G, ENCODING_L, ENCODING_G),
                   (ENCODING_L, ENCODING_L, ENCODING_G, ENCODING_G, ENCODING_G, ENCODING_L),
                   (ENCODING_L, ENCODING_G, ENCODING_L, ENCODING_L, ENCODING_G, ENCODING_G),
                   (ENCODING_L, ENCODING_G, ENCODING_G, ENCODING_L, ENCODING_L, ENCODING_G),
                   (ENCODING_L, ENCODING_G, ENCODING_G, ENCODING_G, ENCODING_L, ENCODING_L),
                   (ENCODING_L, ENCODING_G, ENCODING_L, ENCODING_G, ENCODING_L, ENCODING_G),
                   (ENCODING_L, ENCODING_G, ENCODING_L, ENCODING_G, ENCODING_G, ENCODING_L),
                   (ENCODING_L, ENCODING_G, ENCODING_G, ENCODING_L, ENCODING_G, ENCODING_L),
                   )

# Used to calculate the checksum number.
CHECKSUM_WEIGHTS = (3, 1, 3, 1, 3, 1, 3, 1, 3, 1,  3,  1,  3,  1,  3,  1, 3)

BARS_PER_SYMBOL = 7 # There are seven bars per digit in EAN code.
GUARD_BARS_LEFT = 3
GUARD_BARS_RIGHT = 3
GUARD_BARS_MIDDLE = 5
GUARD_BARS = GUARD_BARS_LEFT + GUARD_BARS_RIGHT + GUARD_BARS_MIDDLE


def ean_get_encoding_group(digit_or_digits):
    """
    Return a list of encodings to use for the first six digits in
    the EAN code. Input argument is the FIRST digit in your symbol list.
    You may also pass a symbol list, in which case the first element will
    be used.
    """
    if hasattr(digit_or_digits, "__getitem__") and hasattr(digit_or_digits, "__len__") and len(digit_or_digits) > 0:
        digit = int(digit_or_digits[0])
    else:
        digit = int(digit_or_digits)
    if digit < 0 or digit >= len(ENCODING_GROUPS):
        raise InvalidSymbolException(EAN, digit)
    return ENCODING_GROUPS[digit]


def ean_assert_valid_symbols(symbol_list):
    """
    Mostly for internal use. See ean_assert_valid_symbols instead.
    """    
    if len(symbol_list) in (7, 8, 17, 18):
        raise NotImplementedError("only EAN-13 supported right now")
    elif len(symbol_list) not in (12, 13):
        raise ValueError("invalid length of symbol list")
    ret = []
    for c in symbol_list:
        try:
            i = int(c)
        except (ValueError, TypeError):
            raise InvalidSymbolException(Ean, c)
        if i < 0 or i > 9:
            raise InvalidSymbolException(Ean, c)
        ret.append(i)
    lenret = len(ret)
    if lenret == 8:
        ret = ret[:-1]
    elif lenret == 13:
        ret = ret[:-1]
    elif lenret == 18:
        ret = ret[:-1]
    return ret


def ean_add_checksum_symbol(symbol_list):
    """
    Raises InvalidSymbolException or ValueError if the symbol list
    contains invalid symbols or is of the wrong size.
    It returns the symbol_list WITH A NEWLY CALCULATED list checksum digit.
    """
    ret = ean_assert_valid_symbols(symbol_list)
    ret.append(ean_get_checksum_symbol(ret))
    return ret
    

def ean_get_checksum_symbol(symbol_list):
    """
    Return the checksum number (one integer digit 0-9).
    """
    symbol_list = ean_assert_valid_symbols(symbol_list)
    total = 0
    offset = 5 # only for EAN-13, maybe not hardcode this?
    for pos, digit in enumerate(symbol_list):
        total += CHECKSUM_WEIGHTS[pos + offset] * digit
    ret = 10 - (total % 10)
    if ret == 10:
        ret = 0
    return ret


def ean_encode(symbol_list):
    """
    Takes EAN symbols and encodes them to a barcode string.
    Will raise InvalidSymbolException if a symbol can not be encoded.
    """
    symbol_list = ean_add_checksum_symbol(symbol_list)
    grouping = ean_get_encoding_group(symbol_list)
    if len(symbol_list) == 13: # only one so far, more to come (maybe)
        first_symbols = symbol_list[1:7]
        last_symbols = symbol_list[7:]
    else:
        raise NotImplementedError("only EAN-13 implemented so far")
    ret = "101"
    for index, digit in enumerate(first_symbols):
        if index < 0 or index > 5:
            raise Exception("internal error (wrong first symbol index), might be a bug")
        if digit < 0 or digit > 9:
            raise Exception("internal error (wrong first symbol digit), might be a bug")
        ret += grouping[index][digit]
    ret += "01010"
    for digit in last_symbols:
        if digit < 0 or digit > 9:
            raise Exception("internal error (wrong last symbol digit), might be a bug")
        ret += ENCODING_R[digit]
    ret += "101"
    return ret


def ean_decode(s):
    """
    Return a list of symbols from a barcode string.
    """
    s = s[3:-3] # remove left and right guard bars
    lenstr = len(s)
    if lenstr == GUARD_BARS_MIDDLE + BARS_PER_SYMBOL * 12: # only one so far, more to come (maybe)
        s = s[:BARS_PER_SYMBOL * 6] + s[BARS_PER_SYMBOL * 6 + GUARD_BARS_MIDDLE:]
    else:
        raise ValueError("invalid size of bar string for EAN")
    ret = []
    encodings_used = ""
    for index, possible_symbol in enumerate(group_string(s, BARS_PER_SYMBOL)):
        if possible_symbol in ENCODING_L:
            encodings_used += "L"
            ret.append(ENCODING_L.index(possible_symbol))
        elif possible_symbol in ENCODING_G:
            encodings_used += "G"
            ret.append(ENCODING_G.index(possible_symbol))
        elif possible_symbol in ENCODING_R:
            ret.append(ENCODING_R.index(possible_symbol))
        else:
            raise DecodeException("could find encoding group for '%s'"%possible_symbol)
    first_digit = {"LLLLLL": 0,
                   "LLGLGG": 1,
                   "LLGGLG": 2,
                   "LLGGGL": 3,
                   "LGLLGG": 4,
                   "LGGLLG": 5,
                   "LGGGLL": 6,
                   "LGLGLG": 7,
                   "LGLGGL": 8,
                   "LGGLGL": 9,
                   }[encodings_used]
    ret.insert(0, first_digit)
    checksum = ean_get_checksum_symbol(ret)
    if ret[-1] != checksum:
        raise DecodeException("checksum mismatch (%d vs %d)"%(ret[-1], checksum))
    return ean_add_checksum_symbol(ret)


class Ean(Barcode):
    """
    EAN barcode.
    """

    def set_symbols(self, symbol_list):
        Barcode.set_symbols(self, ean_add_checksum_symbol(symbol_list))

    def to_unicode(self):
        return u"".join((u"%d"%i for i in self.get_symbols()))

    def set_from_unicode(self, u):
        self.set_symbols(u)

    @classmethod
    def from_unicode(cls, u):
        return cls(u)

    def encode(self):
        return ean_encode(self.get_symbols())

    @classmethod
    def decode(cls, s):
        return cls(ean_decode(s))

    def get_name(self):
        return "EAN-%d"%len(self.get_symbols())

    def get_bar_geometries(self):
        ret = []
        bars = self.encode()
        lenbars = len(bars)
        if lenbars == GUARD_BARS + BARS_PER_SYMBOL * 12:
            middle = BARS_PER_SYMBOL * 6 + GUARD_BARS_LEFT
        else:
            raise ValueError("invalid size of bar string for EAN")
        each_bar = 0.92 / lenbars
        for index, bar in enumerate(bars):
            if (index < GUARD_BARS_LEFT
                or index >= lenbars - GUARD_BARS_RIGHT
                or (index >= middle and index < middle + GUARD_BARS_MIDDLE)):
                height = 0.9
            else:
                height = 0.79
            ret.append((0.06 + index * each_bar, 0.0, each_bar, height, bool(bar != "0")))
        return ret
        
    def get_unicode_geometries(self):
        ret = []
        bars = self.encode()
        lenbars = len(bars)
        if lenbars == GUARD_BARS + BARS_PER_SYMBOL * 12:
            middle = 6
        else:
            raise ValueError("invalid size of bar string for EAN")
        each_bar = 0.92 / lenbars
        each_symbol = each_bar * BARS_PER_SYMBOL
        text = self.to_unicode()
        left = 0.07 - each_bar * BARS_PER_SYMBOL
        for index, digit in enumerate(text):
            ret.append((left, 0.79, each_symbol - 0.02, 0.2, digit))
            left += each_symbol
            if index == 0:
                left = 0.07 + each_bar * 3
            elif index == middle:
                left += GUARD_BARS_MIDDLE * each_bar
        return ret
            
