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

from xml.sax.saxutils import escape
from StringIO import StringIO
import logging

_logger = logging.getLogger(__file__)

def translate(f,data,indent="",default_indent="    "):
    if not data:
        return
    
    tag = data[0]
    tag_only = len(data) == 1

    try:
        f.write(indent)
        f.write("<")    
        f.write(tag)
            
        if tag_only:        
            f.write("/>\n")
            return
            
        attribs = None    
        value = data[1]        
        
        if len(data) == 3:
            attribs = data[2]
            if attribs:
                for attr_key, attr_value in attribs.items():
                    f.write(" ")
                    f.write(attr_key)
                    f.write('="')
                    f.write(str(attr_value))
                    f.write('"')
    
        if value is None:
            f.write("/>\n")
            return
        
        f.write(">")
        
        if isinstance(value,list):
            f.write("\n")
            for child in value:
                translate(f,child,indent+default_indent)
            f.write(indent)
        elif isinstance(value,tuple):
            f.write("\n")
            translate(f,value,indent+default_indent)
            f.write(indent)
        else:
            f.write(escape(str(value)))
        
        f.write("</")
        f.write(tag)
        f.write(">\n")
        return f
    except Exception,e:
        _logger.error("Error by tag %s" % tag)        
        raise e
    

if __name__ == '__main__':
    sf = StringIO()
    translate(sf,("Test",[
      ("EinfachesUnterElement",),
      ("UnterElementMitString","Eine Zeichenkette"),
      ("UnterElementMitFloat",1.0),
      ("UnterElementMitInteger",1),
      ("UnterElementMitAttributen",None,{"attr1" : 10, "attr2" : "TextWert", "attr3" : 10.1} ),
      ("VerschachteltesUnterElement",("IstVerschachtelt","Ja")),
      ("KomplexesElement",[
         ("UnterElement1VonKomplexesElement","TestWert"),
         ("UnterElement2VonKomplexesElement",[
               ("NochEinUnterElement","Mit Wert")  
            ]) 
      ],{"mit_attribut" : "xyz"})
    ]))
    
    print sf.getvalue()