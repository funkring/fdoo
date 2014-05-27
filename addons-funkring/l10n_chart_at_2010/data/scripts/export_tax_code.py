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

import psycopg2
import re
          
class XmlWriter:    
        
    def __init__(self,fileName):
        self.writer = open(fileName,"w")
        self.indent=""        
        self.level=0
        self.id_pattern = re.compile("[^A-Za-z0-9]")
            
    def enter(self):
        self.level+=1
        self.indent = "".rjust(self.level*2)        
        
    def exit(self):
        self.level-=1
        self.indent = "".rjust(self.level*2)   
        
    def write(self,inStr):
        self.writer.write(self.indent+inStr+"\n")
            
    def getID(self,inCode):
        return "tax_code_%s" % (inCode,)
            
    def writeRecord(self,code,name,sign,parent,info):
        self.write('<record id="' + self.getID(code) + '" model="account.tax.code.template">')
        self.enter()
        self.write('<field name="code">'+code+'</field>')
        self.write('<field name="name">'+name+'</field>')
        self.write('<field name="sign">'+str(sign)+'</field>')
        
        if parent:
            self.write('<field name="parent_id" ref="%s"/>' % (self.getID(parent),))
            
        if info:
            self.write('<field name="info">'+info+'</field>')
        
        self.exit()
        self.write('</record>')                
        self.write('')
    
    def startDocument(self):
        self.write('<?xml version="1.0" encoding="utf-8"?>')
        self.write('<openerp>')
        self.write('<data>')
        self.enter()
    
    def endDocument(self):
        self.exit()        
        self.write('</data>')
        self.write('</openerp>')    
    
    def close(self):
        self.writer.close()
        
        
def main():
    conn_string = "host='primary' dbname='funkring' user='funkring' password='meet9Eel'"
    conn = psycopg2.connect(conn_string)
    cr = conn.cursor()
 
    
    
    w = XmlWriter("../account_tax_code.xml")    
    w.startDocument()
    
    
    cr.execute("SELECT c.code, c.name, c.sign, p.code, c.info " 
               " FROM account_tax_code c " 
               " LEFT JOIN account_tax_code p ON p.id = c.parent_id "               
               " WHERE c.company_id = 1 AND NOT c.id = 1 "
               " ORDER BY c.code  ")
    
    for r in cr.fetchall():
        code = r[0]
        name = r[1]
        sign = r[2]
        parent = r[3]        
        info = r[4]
        if not parent:
            parent  = "ATU30"
        w.writeRecord(code,name,sign,parent,info)
     
    w.endDocument()   
    w.close()   
    

if __name__ == '__main__':
    main()