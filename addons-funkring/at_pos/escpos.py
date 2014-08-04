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

'''
@author: Manuel F Martinez <manpaz@bashlinux.com>
@organization: Bashlinux
@copyright: Copyright (c) 2010 Bashlinux
@license: GPL
'''


import Image
import time
import codecs

from socket import *
from constants import *
from exceptions import *



class Escpos:
    """ ESC/POS Printer object """
    handle    = None
    host      = None    
    width     = 43
    codec     = None
   
    def __init__(self,host,port=9100,in_ep=0x82, out_ep=0x01, encode=None) :
        self.host      = host
        self.port      = 9100
        self.in_ep     = in_ep
        self.out_ep    = out_ep
        self.encode     = None
        
        if not self.encode:
            self.encode=codecs.getencoder("cp850")
        
        self.handle = socket(AF_INET,SOCK_STREAM)        
        self.handle.connect((self.host,self.port))
        
    

    def _raw(self, msg):
        """ Print any of the commands above, or clear text """
        self.handle.send(msg)

    def _check_image_size(self, size):
        """Check and fix the size of the image to 32 bits"""
        if size % 32 == 0:
            return (0, 0)
        else:
            image_border = 32 - (size % 32)
            if (image_border % 2) == 0:
                return (image_border / 2, image_border / 2)
            else:
                return (image_border / 2, (image_border / 2) + 1)


    def _print_image(self, line, size):
        i = 0
        cont = 0
        buffer = ""
       
        self._raw(S_RASTER_N)
        buffer = "%02X%02X%02X%02X" % (((size[0]/size[1])/8), 0, size[1], 0)
        self._raw(buffer.decode('hex'))
        buffer = ""

        while i < len(line):
            hex_string = int(line[i:i+8],2)
            buffer += "%02X" % hex_string
            i += 8
            cont += 1
            if cont % 4 == 0:
                self._raw(buffer.decode("hex"))
                buffer = ""
                cont = 0


    def image(self, img):
        """Parse image and then print it"""
        pixels   = []
        pix_line = ""
        im_left  = ""
        im_right = ""
        switch   = 0
        img_size = [ 0, 0 ]

        im_open = Image.open(img)
        im = im_open.convert("RGB")

        if im.size[0] > 512:
            print  "WARNING: Image is wider than 512 and could be truncated at print time "
        if im.size[1] > 255:
            raise ImageSizeError()

        im_border = self._check_image_size(im.size[0])
        for i in range(im_border[0]):
            im_left += "0"
        for i in range(im_border[1]):
            im_right += "0"

        for y in range(im.size[1]):
            img_size[1] += 1
            pix_line += im_left
            img_size[0] += im_border[0]
            for x in range(im.size[0]):
                img_size[0] += 1
                RGB = im.getpixel((x, y))
                im_color = (RGB[0] + RGB[1] + RGB[2])
                im_pattern = "1X0"
                pattern_len = len(im_pattern)
                switch = (switch - 1 ) * (-1)
                for x in range(pattern_len):
                    if im_color <= (255 * 3 / pattern_len * (x+1)):
                        if im_pattern[x] == "X":
                            pix_line += "%d" % switch
                        else:
                            pix_line += im_pattern[x]
                        break
                    elif im_color > (255 * 3 / pattern_len * pattern_len) and im_color <= (255 * 3):
                        pix_line += im_pattern[-1]
                        break 
            pix_line += im_right
            img_size[0] += im_border[1]

        self._print_image(pix_line, img_size)


    def barcode(self, code, bc, width, height, pos, font):
        """ Print Barcode """
        # Align Bar Code()
        self._raw(TXT_ALIGN_CT)
        # Height
        if height >=2 or height <=6:
            self._raw(BARCODE_HEIGHT)
        else:
            raise BarcodeSizeError()
        # Width
        if width >= 1 or width <=255:
            self._raw(BARCODE_WIDTH)
        else:
            raise BarcodeSizeError()
        # Font
        if font.upper() == "B":
            self._raw(BARCODE_FONT_B)
        else: # DEFAULT FONT: A
            self._raw(BARCODE_FONT_A)
        # Position
        if pos.upper() == "OFF":
            self._raw(BARCODE_TXT_OFF)
        elif pos.upper() == "BOTH":
            self._raw(BARCODE_TXT_BTH)
        elif pos.upper() == "ABOVE":
            self._raw(BARCODE_TXT_ABV)
        else:  # DEFAULT POSITION: BELOW 
            self._raw(BARCODE_TXT_BLW)
        # Type 
        if bc.upper() == "UPC-A":
            self._raw(BARCODE_UPC_A)
        elif bc.upper() == "UPC-E":
            self._raw(BARCODE_UPC_E)
        elif bc.upper() == "EAN13":
            self._raw(BARCODE_EAN13)
        elif bc.upper() == "EAN8":
            self._raw(BARCODE_EAN8)
        elif bc.upper() == "CODE39":
            self._raw(BARCODE_CODE39)
        elif bc.upper() == "ITF":
            self._raw(BARCODE_ITF)
        elif bc.upper() == "NW7":
            self._raw(BARCODE_NW7)
        else:
            raise BarcodeTypeError()
        # Print Code
        if code:
            self._raw(code)
        else:
            raise exception.BarcodeCodeError()
            
    def raw(self, txt):            
        """ Print alpha-numeric text """
        if txt:
            self._raw(txt)
        else:
            raise TextError()

    def encodeText(self,txt):
        if self.encode: 
            res = self.encode(txt,errors="ignore")
            if res:
                txt = res[0]
        return txt
        
    def maxlen(self,txt,maxlen):
        if len(txt) > maxlen:
            txt=txt[:maxlen]
        return txt
            
    def text(self, txt):
        txt = self.encodeText(txt)            
        self.raw(txt)

    def rtext(self, txt, width=1.0, overflow=None):
        txt = self.encodeText(txt)
        chars = int(width*self.width)
        if overflow and len(txt) > chars:
            self.text(overflow)        
        else:
            txt = self.maxlen(txt,chars)    
            txt = txt.rjust(chars)
        self.raw(txt)
        
    def tryRtext(self, txt, width=1.0):
        txt = self.encodeText(txt)
        chars = int(width*self.width)        
        txt = self.maxlen(txt,chars)    
        txt = txt.rjust(chars)
        self.raw(txt)
        
    def ltext(self, txt, width=1.0):
        txt = self.encodeText(txt)        
        chars = int(width*self.width)
        txt = self.maxlen(txt,chars)    
        txt = txt.ljust(chars)
        self.raw(txt)

    def line(self,width=1.0):
        chars = int(width*self.width)
        self.raw("".ljust(chars-1,"\xc4"))
        
    def set(self, align='left', font='a', type='normal', width=1, height=1):
        """ Set text properties """
        # Align
        if align.upper() == "CENTER":
            self._raw(TXT_ALIGN_CT)
        elif align.upper() == "RIGHT":
            self._raw(TXT_ALIGN_RT)
        elif align.upper() == "LEFT":
            self._raw(TXT_ALIGN_LT)
        # Font
        if font.upper() == "B":
            self._raw(TXT_FONT_B)
        else:  # DEFAULT FONT: A
            self._raw(TXT_FONT_A)
        # Type
        if type.upper() == "B":
            self._raw(TXT_BOLD_ON)
            self._raw(TXT_UNDERL_OFF)
        elif type.upper() == "U":
            self._raw(TXT_BOLD_OFF)
            self._raw(TXT_UNDERL_ON)
        elif type.upper() == "U2":
            self._raw(TXT_BOLD_OFF)
            self._raw(TXT_UNDERL2_ON)
        elif type.upper() == "BU":
            self._raw(TXT_BOLD_ON)
            self._raw(TXT_UNDERL_ON)
        elif type.upper() == "BU2":
            self._raw(TXT_BOLD_ON)
            self._raw(TXT_UNDERL2_ON)
        elif type.upper == "NORMAL":
            self._raw(TXT_BOLD_OFF)
            self._raw(TXT_UNDERL_OFF)
        # Width
        if width == 2 and height != 2:
            self._raw(TXT_NORMAL)
            self._raw(TXT_2WIDTH)
        elif height == 2 and width != 2:
            self._raw(TXT_NORMAL)
            self._raw(TXT_2HEIGHT)
        elif height == 2 and width == 2:
            self._raw(TXT_2WIDTH)
            self._raw(TXT_2HEIGHT)
        else: # DEFAULT SIZE: NORMAL
            self._raw(TXT_NORMAL)


    def cut(self, mode=''):
        """ Cut paper """
        # Fix the size between last line and cut
        # TODO: handle this with a line feed
        self._raw("\n\n\n\n\n\n")
        if mode.upper() == "PART":
            self._raw(PAPER_PART_CUT)
        else: # DEFAULT MODE: FULL CUT
            self._raw(PAPER_FULL_CUT)


    def cashdraw(self, pin):
        """ Send pulse to kick the cash drawer """
        if pin == 2:
            self._raw(CD_KICK_2)
        elif pin == 5:
            self._raw(CD_KICK_5)
        else:
            raise CashDrawerError()


    def hw(self, hw):
        """ Hardware operations """
        if hw.upper() == "INIT":
            self._raw(HW_INIT)
        elif hw.upper() == "SELECT":
            self._raw(HW_SELECT)
        elif hw.upper() == "RESET":
            self._raw(HW_RESET)
        else: # DEFAULT: DOES NOTHING
            pass


    def control(self, ctl):
        """ Feed control sequences """
        if ctl.upper() == "LF":
            self._raw(CTL_LF)
        elif ctl.upper() == "FF":
            self._raw(CTL_FF)
        elif ctl.upper() == "CR":
            self._raw(CTL_CR)
        elif ctl.upper() == "HT":
            self._raw(CTL_HT)
        elif ctl.upper() == "VT":
            self._raw(CTL_VT)

    def close(self):      
        if self.handle:            
            self.handle.close()            
            self.handle = None
    
    def __del__(self):
        """ Release device interface """
        self.close()
            
            

if __name__ == '__main__':
    printer = Escpos("dev-kassa")    
    printer.cashdraw(2)    
    printer.hw("INIT")
    printer.set(align="center",height=2,width=2)
    #printer.set(align="center",height=2,width=2)
    printer.text("Labonca Biohof\n\n")
    printer.set(align="center",height=1,width=1)
    printer.text("Labonca OG\n")
    printer.text("A-8291 Burgau 54\n")
    printer.text("office@labonca.at\n")
    printer.text("www.labonca-biohof.at\n")
    printer.text("\n\n\n\n")
        
    printer.set(align='left',height=1,width=1)
    
    printer.ltext("POS/4272", 0.5)
    printer.rtext("2011-07-27 17:58:16", 0.5)
    printer.text("\n\n")
    
    col1 = 0.5
    col2 = 0.3
    col3 = 0.2 
    
    printer.ltext("Eier Hälik 6er",col1)
    printer.rtext("2,000 Stk",col2)
    printer.rtext("400,20",col3)
    printer.text("\n")
    
    printer.ltext("Eier Hälik 6er Noch längerer Namen",col1)
    printer.rtext("2,000 Stk",col2)
    printer.rtext("400,20",col3)
    printer.text("\n")
    
#    printer.text("Eier Hälik 6er       2,000 Stk  400,20 EUR\n")
#    printer.text("Eier Holik 6er       2,000 Stk  400,20 EUR\n")
#    printer.text("Eier Holik 6er       2,000 Stk  400,20 EUR\n")
#    printer.text("Eier Holik 6er       2,000 Stk  400,20 EUR\n")
    
    printer.set(align='left',type="u2")
    printer.line()
    printer.ltext("GESAMT BRUTTO",col1)
    printer.rtext("EUR",col2)
    printer.rtext("800,40",col3)
    printer.text("\n")
    printer.ltext("inkl. UST 10%",col1)
    printer.rtext("EUR",col2)
    printer.rtext("2,29",col3)       
    printer.text("\n")
    printer.cut()
    printer.close()