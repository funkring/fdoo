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
            
    def getID(self,inName):
        return "fpos_%s" % (re.sub("[^A-Za-z0-9_]", "", inName.lower()),)
    
    def getTaxID(self,inName):
        return "tax_%s" % (re.sub("[^A-Za-z0-9]", "", inName.lower().replace("steuer","")),)
        
    def getAccountID(self,inCode):
        return "chart"+inCode
            
    def getTaxCodeID(self,inCode):
        return "tax_code_%s" % (inCode,)
                
    def writeRecord(self,name):
        self.write('<record id="' + self.getID(name) + '" model="account.fiscal.position.template">')
        self.enter()
        self.write('<field name="chart_template_id" ref="austria_chart_template"/>')
        self.write('<field name="name">%s</field>' % (name,))        
        self.exit()
        self.write('</record>')                
        self.write('')
    
    def writeTaxRecord(self,fpos,src_tax,dest_tax):
        self.write('<record id="' + self.getID(fpos + "_" +src_tax) + '" model="account.fiscal.position.tax.template">')
        self.enter()
        self.write('<field name="position_id" ref="%s"/>' % (self.getID(fpos),))        
        self.write('<field name="tax_src_id" ref="%s"/>' % (self.getTaxID(src_tax),))
        if dest_tax:
            self.write('<field name="tax_dest_id" ref="%s"/>' % (self.getTaxID(dest_tax),))        
        self.exit()
        self.write('</record>')                
        self.write('')
        
    def writeAccountRecord(self,fpos,src_account,dest_account):
        self.write('<record id="' + self.getID(fpos + "_" +src_account) + '" model="account.fiscal.position.account.template">')
        self.enter()
        self.write('<field name="position_id" ref="%s"/>' % (self.getID(fpos),))        
        self.write('<field name="account_src_id" ref="%s"/>' % (self.getAccountID(src_account),))
        if dest_account:
            self.write('<field name="account_dest_id" ref="%s"/>' % (self.getAccountID(dest_account),))        
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
 
    
    
    w = XmlWriter("../account_fpos.xml")    
    w.startDocument()
    
    
    cr.execute("SELECT name FROM account_fiscal_position WHERE company_id=1 ")
    for r in cr.fetchall():
        name = r[0]               
        w.writeRecord(name)

    cr.execute("SELECT f.name, t1.name, t2.name " 
               " FROM account_fiscal_position_tax ft "
               " INNER JOIN account_fiscal_position f ON f.id = ft.position_id AND f.company_id = 1 "
               " LEFT JOIN account_tax t1 ON t1.id = ft.tax_src_id " 
                "LEFT JOIN account_tax t2 ON t2.id = ft.tax_dest_id ")
    for r in cr.fetchall():
        w.writeTaxRecord(r[0],r[1],r[2])
     
     
    cr.execute("SELECT f.name, a1.code, a2.code "
        " FROM account_fiscal_position_account fa " 
        " INNER JOIN account_fiscal_position f ON f.id = fa.position_id AND f.company_id = 1 "
        " LEFT JOIN account_account a1 ON a1.id = fa.account_src_id "
        " LEFT JOIN account_account a2 ON a2.id = fa.account_dest_id ")
    for r in cr.fetchall():
        w.writeAccountRecord(r[0],r[1],r[2])
     
    w.endDocument()   
    w.close()   
    

if __name__ == '__main__':
    main()