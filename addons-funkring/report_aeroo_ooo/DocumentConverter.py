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
DEFAULT_BUFSIZE = 4096
DEFAULT_TIMEOUT = 30

import socket

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from os.path import abspath
from os.path import isfile
from os.path import splitext
import sys
import logging
from openerp import tools
from openerp.tools.translate import _

import simplejson

_logger = logging.getLogger(__name__)

class DocumentConversionException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message


class DocumentConverter:

    def __init__(self, host='localhost', port=DEFAULT_OPENOFFICE_PORT):
        self._open = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setblocking(1)
        self._socket.settimeout(DEFAULT_TIMEOUT)
        self._socket.connect((host,port))
        self._fd = self._socket.makefile("rw",DEFAULT_BUFSIZE)
        # Initialize
        _logger.debug("DocumentConverter->Initialize")
        self._call()
        _logger.debug("DocumentConverter->Initialized")

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
        self._fd.write(header.encode("utf-8"))
        if data:
            self._fd.write(data)
        self._fd.flush()

    def _read(self):
        res = self._fd.readline()
        if not res:
            raise DocumentConversionException("Connection closed")

        header = res.decode("utf-8")
        header = simplejson.loads(header)
        data = None
        length = header.get("length")
        if length:
            _logger.info("Read document with length=%s" % length)
            data = self._fd.read(length)
            if not data:
                raise DocumentConversionException("Connection closed")

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
            _logger.debug("Close DocumentConverter")
            try:
                self._call("close")                
            except Exception as e:
                _logger.error("Unable to close! %s" % str(e))
            finally:
                try:
                    self._socket.close()
                except Exception as e:
                    _logger.error("Unable to close socket! %s" % str(e))

    def putDocument(self, data):
        _logger.debug("DocumentConverter->putDocument")
        self._call("putDocument",data)

    def closeDocument(self):
        _logger.debug("DocumentConverter->closeDocument")
        self._call("closeDocument")

    def printDocument(self,printer=None):
        self._call("printDocument",param={"printer":printer})

    # replace of saveByStream
    def getDocument(self, filter_name=None):
        _logger.debug("DocumentConverter->getDocument")
        return self._call("getDocument",param={"filter":filter_name})

    def readDocumentFromStreamAndClose(self, filter_name=None):
        _logger.debug("DocumentConverter->readDocumentFromStreamAndClose")
        try:
            doc = self.getDocument(filter_name)
            return doc
        finally:
            self.close()
        
#         self._send("streamDocument",param={"filter":filter_name})
#         """ read current document from stream and close """
#         try:
#             return self._fd.read()
#         finally:
#             self._open = False
#             try:
#                 self._socket.close()
#             except Exception as e:
#                 _logger.exception(e)

    def insertSubreports(self, oo_subreports):
        _logger.debug("DocumentConverter->insertSubreports")
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
        _logger.debug("DocumentConverter->joinDocument")
        while docs:
            self._call("addDocument",docs.pop())

