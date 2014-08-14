#!/usr/bin/env python
#
# PyODConverter (Python OpenDocument Converter) v1.0.0 - 2008-05-05
#
# This script converts a document from one office format to another by
# connecting to an OpenOffice.org instance via Python-UNO bridge.
#
# Copyright (C) 2008 Mirko Nasato <mirko@artofsolving.com>
#                    Matthew Holloway <matthew@holloway.co.nz>
#                    KN dati Ltd (www.kndati.lv) 
# Licensed under the GNU LGPL v2.1 - http://www.gnu.org/licenses/lgpl-2.1.html
# - or any later version.
#

DEFAULT_OPENOFFICE_PORT = 8100

import socket

try:
    from cStringIO import StringIO
except:    
    from StringIO import StringIO

from os.path import abspath
from os.path import isfile
from os.path import splitext
import sys
from openerp import tools
from openerp.tools.translate import _

import simplejson

class DocumentConversionException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message


class DocumentConverter:
    
    def __init__(self, host='localhost', port=DEFAULT_OPENOFFICE_PORT):
        self._open = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host,port))
        # Initialize
        self._call() 
        
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.close()
        
    def __del__(self):
        self.close()
            
    def _send(self, fnct=None, data=None, param=None):
        if not param:
            param = {}
        if fnct:
            param["fnct"]=fnct
        if data:
            param["length"]=len(data) 
        
        header = "%s\n" % simplejson.dumps(param)
        self._socket.sendall(header.encode("utf-8"))
        if data:
            self._socket.sendall(data)
   
    def _read(self):
        header = self._socket.recv(4096)
        header = header.decode("utf-8")
        header = simplejson.loads(header)
        data = None
        length = header.get("length")
        if length:
            data = self._socket.recv(length)
        
        error = header.get("error")
        if error:
            raise DocumentConversionException(header.get("message"))
        
        return data
    
    def _call(self, fnct=None, data=None, param=None):
        self._send(fnct=fnct, data=data, param=param)
        return self._read()
    
    def close(self):
        if self._open:
            self._open=False            
            try:
                self._call("close")
                self._socket.close()
            except:
                pass

    def putDocument(self, data):
        self._call("putDocument",data)

    def closeDocument(self):
        self._call("closeDocument")

    def printDocument(self,printer=None):
        self._call("printDocument",param={"printer":printer})          
        
    # replace of saveByStream
    def getDocument(self, filter_name=None):
        return self._call("getDocument",param={"filter":filter_name})

    def insertSubreports(self, oo_subreports):
        """
        Inserts the given file into the current document.
        The file contents will replace the placeholder text.
        """
        for subreport in oo_subreports:            
            fd = file(subreport, 'rb')
            with fd:
                subdata = fd.read()
                self._call("insertDocument",subdata, param={"name":subreport})

    def joinDocuments(self, docs):
        while(docs):
            self._call("adddDocument",docs.pop())

