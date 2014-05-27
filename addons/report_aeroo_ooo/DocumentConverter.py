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

from os.path import abspath
from os.path import isfile
from os.path import splitext
import sys
from StringIO import StringIO
from openerp import tools

import uno
import unohelper
from com.sun.star.beans import PropertyValue
from com.sun.star.uno import Exception as UnoException
from com.sun.star.connection import NoConnectException, ConnectionSetupException
from com.sun.star.beans import UnknownPropertyException
from com.sun.star.lang import IllegalArgumentException
from com.sun.star.io import XOutputStream
from com.sun.star.io import IOException
from openerp.tools.translate import _

class DocumentConversionException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class OutputStreamWrapper(unohelper.Base, XOutputStream):
    """ Minimal Implementation of XOutputStream """
    def __init__(self, debug=True):
        self.debug = debug
        self.data = StringIO()
        self.position = 0
        if self.debug:
            sys.stderr.write("__init__ OutputStreamWrapper.\n")

    def writeBytes(self, bytes):
        if self.debug:
            sys.stderr.write("writeBytes %i bytes.\n" % len(bytes.value))
        self.data.write(bytes.value)
        self.position += len(bytes.value)

    def close(self):
        if self.debug:
            sys.stderr.write("Closing output. %i bytes written.\n" % self.position)
        self.data.close()

    def flush(self):
        if self.debug:
            sys.stderr.write("Flushing output.\n")
        pass
    def closeOutput(self):
        if self.debug:
            sys.stderr.write("Closing output.\n")
        pass

class DocumentConverter:
   
    def __init__(self, host='localhost', port=DEFAULT_OPENOFFICE_PORT):
        self._host = host
        self._port = port
        self._localContext= uno.getComponentContext()
        self._localServiceManager = self._localContext.ServiceManager
        self._localResolver = self._localServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", self._localContext)
        self._desktop = None
        try:
            self._context = self._localResolver.resolve("uno:socket,host=%s,port=%s;urp;StarOffice.ComponentContext" % (host, port))
            self._desktop = self._context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self._context)
        except IllegalArgumentException, exception:
            raise DocumentConversionException("The url is invalid (%s)" % exception)
        except NoConnectException, exception:
            raise DocumentConversionException("Failed to connect to OpenOffice.org on host %s, port %s. %s" % (host, port, exception))
        except ConnectionSetupException, exception:
            raise DocumentConversionException("Not possible to accept on a local resource (%s)" % exception)
       
    #def __del__(self):
        #if self._desktop:
        #    self._desktop.terminate()

    def putDocument(self, data):
        inputStream = self._context.ServiceManager.createInstanceWithContext("com.sun.star.io.SequenceInputStream", self._context)
        inputStream.initialize((uno.ByteSequence(data),))
        self.document = self._desktop.loadComponentFromURL('private:stream', "_blank", 0, self._toProperties(InputStream = inputStream))
        inputStream.closeInput()
        
    def closeDocument(self):
        self.document.close(True)

    def printDocument(self,printer=None):          
       if printer:
           p = PropertyValue()
           p.Name=u"Name"           
           p.Value = tools.ustr(printer)
           uno.invoke(self.document,"setPrinter",((p,),))
                         
       p = PropertyValue()
       p.Name = u"Wait"
       p.Value = True              
       uno.invoke(self.document, "print", ((p,),))        
       
       
    def refresh(self, document):
        # At first update Table-of-Contents.
        # ToC grows, so page numbers grows too.
        # On second turn update page numbers in ToC
        try:
            document.refresh()
            indexes = document.getDocumentIndexes()
            for i in range(0, indexes.getCount()):
                indexes.getByIndex(i).update()
        except AttributeError, e: # ods document does not support refresh
            # the document doesn't implement the XRefreshable and/or
            # XDocumentIndexesSupplier interfaces
            pass
       
    def saveByStream(self, filter_name=None):
        # refresh document before saving
        self.refresh(self.document)
        outputStream = OutputStreamWrapper(False)
        try:
            self.document.storeToURL('private:stream', self._toProperties(OutputStream = outputStream, FilterName = filter_name))
            #if output=='pdf':
            #    self.document.storeToURL('private:stream', self._toProperties(OutputStream = outputStream, FilterName = "writer_pdf_Export"))
            #elif output=='doc':
            #    self.document.storeToURL('private:stream', self._toProperties(OutputStream = outputStream, FilterName = "MS Word 97"))
            #elif output=='xls':
            #    self.document.storeToURL('private:stream', self._toProperties(OutputStream = outputStream, FilterName = "MS Excel 97"))
            #else:
            #    self.document.storeToURL('private:stream', self._toProperties(OutputStream = outputStream))
        except IOException, e:
            print ("IOException during conversion: %s - %s" % (e.ErrCode, e.Message))
            outputStream.close()

        openDocumentBytes = outputStream.data.getvalue()
        outputStream.close()
        return openDocumentBytes
        

    def insertSubreports(self, oo_subreports):
        """
        Inserts the given file into the current document.
        The file contents will replace the placeholder text.
        """
        import os

        for subreport in oo_subreports:
            fd = file(subreport, 'rb')
            placeholder_text = "<insert_doc('%s')>" % subreport
            subdata = fd.read()
            subStream = self._context.ServiceManager.createInstanceWithContext("com.sun.star.io.SequenceInputStream", self._localContext)
            subStream.initialize((uno.ByteSequence(subdata),))

            search = self.document.createSearchDescriptor()
            search.SearchString = placeholder_text
            found = self.document.findFirst( search )
            while found:
                try:
                    found.insertDocumentFromURL('private:stream', self._toProperties(InputStream = subStream, FilterName = "writer8"))
                except Exception, ex:
                    print (_("Error inserting file %s on the OpenOffice document: %s") % (subreport, ex))
                found = self.document.findNext(found, search)

            os.unlink(subreport)

    def joinDocuments(self, docs):
        while(docs):
            subStream = self._context.ServiceManager.createInstanceWithContext("com.sun.star.io.SequenceInputStream", self._localContext)
            subStream.initialize((uno.ByteSequence(docs.pop()),))
            try:
                self.document.Text.getEnd().insertDocumentFromURL('private:stream', self._toProperties(InputStream = subStream, FilterName = "writer8"))
            except Exception, ex:
                print (_("Error inserting file %s on the OpenOffice document: %s") % (docs, ex))

    def convertByPath(self, inputFile, outputFile):
        inputUrl = self._toFileUrl(inputFile)
        outputUrl = self._toFileUrl(outputFile)
        document = self._desktop.loadComponentFromURL(inputUrl, "_blank", 8, self._toProperties(Hidden=True))
        # refresh document
        self.refresh(document)
        try:
            document.storeToURL(outputUrl, self._toProperties(FilterName="writer_pdf_Export"))
        finally:
            document.close(True)

    def _toFileUrl(self, path):
        return uno.systemPathToFileUrl(abspath(path))

    def _toProperties(self, **args):
        props = []
        for key in args:
            prop = PropertyValue()
            prop.Name = key
            prop.Value = args[key]
            props.append(prop)
        return tuple(props)

