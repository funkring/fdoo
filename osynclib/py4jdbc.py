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

from py4j.java_gateway import JavaGateway
import logging
import sys

_logger = logging.getLogger(__name__)

class JdbcCursor(object):
    
    def __init__(self, inDriver, inUrl):
        self.jgw = JavaGateway()        
        self.jcr = self.jgw.entry_point.createCursor(inDriver,inUrl)
    
         
    @property
    def description(self):
        return eval(self.jcr.description())
   
    def close(self):
        try:
            try:
                if self.jcr:
                    self.jcr.close()
            finally:
                if self.jgw:
                    self.jgw.close()
                
        except:
            _logger.error("Unable to close py4jdbc cursor: %s" % (sys.exc_info()[0],))
        finally:
            self.jgw = None
            self.jcr = None
    
    # TODO: this is a possible way to close the open result sets
    # but I'm not sure when __del__ will be called
    __del__ = close

    def execute(self, operation, parameters=None):
        query = parameters and operation % parameters or operation
        self.jcr.execute(query)

    def executemany(self, operation, seq_of_parameters):
        raise NotImplementedError("executemany(...) is not implemented")

    def fetchone(self):
        res = self.jcr.fetchone()
        return res and eval(res) or None
        
    def fetchmany(self, size=None):
        res = self.jcr.fetchmany(size)
        return res and eval(res) or None
        
    def fetchall(self):
        res = self.jcr.fetchall()
        return res and eval(res) or None
    
    def setMaxRows(self,rows):
        self.jcr.setMaxRows(rows)
    
    
if __name__ == '__main__':
    cr = JdbcCursor("jdbc.gupta.sqlbase.SqlbaseDriver","jdbc:sqlbase://192.168.1.27/TESTWAWI;user=SYSADM")
    #cr = JdbcCursor("org.postgresql.Driver","jdbc:postgresql://127.0.0.1/openerp7_funkring;user=martin")
    try:
        cr.setMaxRows(10)
        cr.execute("SELECT * FROM HW_FORMAT")
        print cr.description
        for row in cr.fetchmany(10):
            print row
    finally:
        cr.close()
    print "Closed!"
