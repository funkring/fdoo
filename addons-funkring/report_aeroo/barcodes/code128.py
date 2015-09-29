# -*- coding: utf-8 -*-
"""
Barcodes for Python, Code-128 package
Copyright 2009  Peter Gebauer

Code-128 implementation of barcodes. Supportes A, B and C.
Set A is still missing a lot of the weird codes (DLE, DC*, FF, VT and so on...),
but that's just because I'll never use them. Only DEL and NUL are supported so
far via ASCII symbols.


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

BARS_PER_SYMBOL = 11
GUARD_BARS_RIGHT = 2
QUIET_ZONE = 12

CODEPOINTS_A = (
    list(" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_\0")
    + [None] * 31 + ["FNC3", "FNC2", "SHIFT_B", "CODE_C", "CODE_B", "FNC4"]
    + ["FNC1", "START_A", "START_B", "START_C", "STOP"]
    )
CODEPOINTS_B = (
    list(" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\127")
    + ["FNC3", "FNC2", "SHIFT_A", "CODE_C", "FNC4", "CODE_A"]
    + ["FNC1", "START_A", "START_B", "START_C", "STOP"]
    )
CODEPOINTS_C = (
    ["%02d"%i for i in xrange(100)]
    + ["CODE_B", "CODE_A"]
    + ["FNC1", "START_A", "START_B", "START_C", "STOP"]
    )

CONTROL_STRINGS = ("CODE_A", "CODE_B", "CODE_C", "START_A", "START_B", "START_C", "STOP",
                   "FNC1", "FNC2", "FNC3", "FNC4", "SHIFT_A", "SHIFT_B",)

CODEPOINTS = {"A": CODEPOINTS_A, "B": CODEPOINTS_B, "C": CODEPOINTS_C}

ENCODINGS = (
    "11011001100", # 0
    "11001101100", # 1
    "11001100110", # 2
    "10010011000", # 3
    "10010001100", # 4
    "10001001100", # 5
    "10011001000", # 6
    "10011000100", # 7
    "10001100100", # 8
    "11001001000", # 9
    "11001000100", # 10
    "11000100100", # 11
    "10110011100", # 12
    "10011011100", # 13
    "10011001110", # 14
    "10111001100", # 15
    "10011101100", # 16
    "10011100110", # 17
    "11001110010", # 18
    "11001011100", # 19
    "11001001110", # 20
    "11011100100", # 21
    "11001110100", # 22
    "11101101110", # 23
    "11101001100", # 24
    "11100101100", # 25
    "11100100110", # 26
    "11101100100", # 27
    "11100110100", # 28
    "11100110010", # 29
    "11011011000", # 30
    "11011000110", # 31
    "11000110110", # 32
    "10100011000", # 33
    "10001011000", # 34
    "10001000110", # 35
    "10110001000", # 36
    "10001101000", # 37
    "10001100010", # 38
    "11010001000", # 39
    "11000101000", # 40
    "11000100010", # 41
    "10110111000", # 42
    "10110001110", # 43
    "10001101110", # 44
    "10111011000", # 45
    "10111000110", # 46
    "10001110110", # 47
    "11101110110", # 48
    "11010001110", # 49
    "11000101110", # 50
    "11011101000", # 51
    "11011100010", # 52
    "11011101110", # 53
    "11101011000", # 54
    "11101000110", # 55
    "11100010110", # 56
    "11101101000", # 57
    "11101100010", # 58
    "11100011010", # 59
    "11101111010", # 60
    "11001000010", # 61
    "11110001010", # 62
    "10100110000", # 63
    "10100001100", # 64
    "10010110000", # 65
    "10010000110", # 66
    "10000101100", # 67
    "10000100110", # 68
    "10110010000", # 69
    "10110000100", # 70
    "10011010000", # 71
    "10011000010", # 72
    "10000110100", # 73
    "10000110010", # 74
    "11000010010", # 75
    "11001010000", # 76
    "11110111010", # 77
    "11000010100", # 78
    "10001111010", # 79
    "10100111100", # 80
    "10010111100", # 81
    "10010011110", # 82
    "10111100100", # 83
    "10011110100", # 84
    "10011110010", # 85
    "11110100100", # 86
    "11110010100", # 87
    "11110010010", # 88
    "11011011110", # 89
    "11011110110", # 90
    "11110110110", # 91
    "10101111000", # 92
    "10100011110", # 93
    "10001011110", # 94
    "10111101000", # 95
    "10111100010", # 96
    "11110101000", # 97
    "11110100010", # 98
    "10111011110", # 99 CODE C if A or B
    "10111101110", # 100 CODE B if C
    "11101011110", # 101 CODE A if C
    "11110101110", # 102 FNC1
    "11010000100", # 103 CODE_START A
    "11010010000", # 104 CODE_START B
    "11010011100", # 105 CODE_START C
    "11000111010", # 106 CODE_STOP
    )

def code128_get_set_name(codepoints):
    """
    Returns the set name for the specified codepoints.
    Return value is "A", "B", "C" or None if unknown.
    """
    if codepoints == CODEPOINTS_A:
        return "A"
    elif codepoints == CODEPOINTS_B:
        return "B"
    elif codepoints == CODEPOINTS_C:
        return "C"
    return None


def code128_strings_to_symbols(string_list):
    """
    Converts a sequence of strings to a sequence of symbols.
    """
    ret = []
    codepoints = None
    for s in string_list:
        if codepoints:            
            if s in codepoints:
                ret.append(codepoints.index(s))
            else:
                raise ValueError("unable to find symbol for string '%s' in set %s"%(s, code128_get_set_name(codepoints)))
            if s == "CODE_A":
                codepoints = CODEPOINTS_A
            elif s == "CODE_B":
                codepoints = CODEPOINTS_B
            elif s == "CODE_C":
                codepoints = CODEPOINTS_C
        elif s == "START_A":
            codepoints = CODEPOINTS_A
            ret.append(codepoints.index(s))
        elif s == "START_B":
            codepoints = CODEPOINTS_B
            ret.append(codepoints.index(s))
        elif s == "START_C":
            codepoints = CODEPOINTS_C
            ret.append(codepoints.index(s))
        else:
            raise ValueError("first element must be 'START_A', 'START_B' or 'START_C'")
    return ret


def code128_symbols_to_strings(symbol_list):
    """
    Converts a sequence of symbols to a sequence of strings.
    """
    ret = []
    codepoints = None
    for symbol in symbol_list:
        if codepoints:
            if symbol < 0 or symbol > 106:
                raise InvalidSymbolException(Code128, symbol)
            ret.append(codepoints[symbol])
            if symbol == 106:
                break
            elif symbol in (103, 104, 105):
                raise InvalidSymbolException(Code128, symbol, "code start symbols may only occur once in the beginning")
            elif codepoints[symbol] == "CODE_A":
                codepoints = CODEPOINTS_A
            elif codepoints[symbol] == "CODE_B":
                codepoints = CODEPOINTS_B
            elif codepoints[symbol] == "CODE_C":
                codepoints = CODEPOINTS_C
        elif symbol == 103:
            codepoints = CODEPOINTS_A
            ret.append(codepoints[symbol])
        elif symbol == 104:
            codepoints = CODEPOINTS_B
            ret.append(codepoints[symbol])
        elif symbol == 105:
            codepoints = CODEPOINTS_C
            ret.append(codepoints[symbol])
        else:
            raise InvalidSymbolException(Code128, None, "no valid code start symbol found")
    return ret


def code128_assert_valid_symbols(symbol_list):
    """
    Makes sure all symbols are valid, returns the symbol list for easier use.
    """
    codepoints = None
    for symbol in symbol_list:
        if codepoints:
            if symbol < 0 or symbol > 106:
                raise InvalidSymbolException(Code128, symbol)
            elif codepoints[symbol] == "CODE_A":
                codepoints = CODEPOINTS_A
            elif codepoints[symbol] == "CODE_B":
                codepoints = CODEPOINTS_B
            elif codepoints[symbol] == "CODE_C":
                codepoints = CODEPOINTS_C
        else:
            if symbol == 103:
                codepoints = CODEPOINTS_A
            elif symbol == 104:
                codepoints = CODEPOINTS_B
            elif symbol == 105:
                codepoints = CODEPOINTS_C
            else:
                raise InvalidSymbolException(Code128, None, "no valid code start symbol found")
    if symbol_list and not symbol_list[-1] == 106:
        raise InvalidSymbolException(Code128, None, "no valid stop code symbol found")
    return symbol_list


def code128_get_checksum_symbol(symbol_list):
    """
    Returns the checksum symbol (0-103).
    """
    total = 0
    for weight, symbol in enumerate(symbol_list):
        if weight > 0 and symbol < 103:
            total += weight * symbol
        elif symbol >= 103 and symbol < 106:
            total += symbol
        elif symbol != 106:
            raise InvalidSymbolException(Code128, symbol)
    return total % 103


def code128_encode(symbol_list):
    """
    Encodes the symbol list into a bars string.
    """
    ret = []
    symbol_list = code128_assert_valid_symbols(symbol_list)
    for symbol in symbol_list:        
        ret.append(ENCODINGS[symbol])
    ret.insert(-1, ENCODINGS[code128_get_checksum_symbol(symbol_list)])
    ret.append("1" * GUARD_BARS_RIGHT) # termination bars
    return "".join(ret)


def code128_decode(s):
    """
    Decodes a bars string into a symbol list.
    """
    ret = []
    s = s[:-GUARD_BARS_RIGHT] # remove termination bars
    if len(s) % BARS_PER_SYMBOL != 0:
        raise ValueError("invalid number of bars")
    for s in group_string(s, BARS_PER_SYMBOL, True):
        if s in ENCODINGS:
            ret.append(ENCODINGS.index(s))
        else:
            raise DecodeException("could not find encoding for bars '%s'"%s)
    if len(ret) < 3:
        raise DecodeException("symbol list too short")
    checksum1 = ret[-2]
    del ret[-2]
    ret = code128_assert_valid_symbols(ret)
    checksum2 = code128_get_checksum_symbol(ret)
    if checksum1 != checksum2:
        raise DecodeException("checksum mismatch (%d vs %d)"%(checksum1, checksum2))
    return ret


class Code128(Barcode):
    """
    Code128-A, B and C.
    """

    def set_symbols(self, symbol_list):
        Barcode.set_symbols(self, code128_assert_valid_symbols(symbol_list))

    @classmethod
    def from_strings(cls, string_list):
        """
        Returns a Code128 instance from a sequence of strings.
        """
        return cls(code128_strings_to_symbols(string_list))

    def to_strings(self):
        return code128_symbols_to_strings(self.get_symbols())

    def set_from_strings(self, string_list):
        self.set_symbols(code128_strings_to_symbols(string_list))

    def encode(self):
        return code128_encode(self.get_symbols())

    @classmethod
    def decode(cls, s):
        return cls(code128_decode(s))

    def to_unicode(self):
        ret = []
        strings = code128_symbols_to_strings(self.get_symbols())
        for s in strings:
            if not s in CONTROL_STRINGS:
                ret.append(unicode(s))
        return u"".join(ret)
                    
    @classmethod
    def from_unicode(cls, u):
        return cls.from_strings(["START_B"] + list(u) + ["STOP"])

    def set_from_unicode(self, u):
        self.set_from_strings(["START_B"] + list(u) + ["STOP"])

    def get_name(self):
        """
        Returns the full name of the barcode standard.
        """
        syms = self.get_symbols()
        if syms:
            sym = syms[0]
            if sym == 103:
                return "Code128A"
            elif sym == 104:
                return "Code128B"
            elif sym == 105:
                return "Code128C"
            raise Exception("this shouldn't happen, invalid start code")
        raise ValueError("empty Code128, unable to determine type")
            
    def get_bar_geometries(self):
        ret = []
        bars = "0" * QUIET_ZONE + self.encode() + "0" * QUIET_ZONE
        each_bar = 1.0 / len(bars)
        for index, bar in enumerate(bars):            
            ret.append((0.0 + index * each_bar, 0.0, each_bar, 0.75, bool(bar != "0")))
        return ret
        
    def get_unicode_geometries(self):
        return [(0.0, 0.75, 1.0, 0.2, self.to_unicode())]
