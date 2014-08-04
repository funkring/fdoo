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
          
class XmlWriter:    
        
    def __init__(self,fileName):
        self.writer = open(fileName,"w")
        self.indent=""        
        self.level=0
        
    def enter(self):
        self.level+=1
        self.indent = "".rjust(self.level*2)        
        
    def exit(self):
        self.level-=1
        self.indent = "".rjust(self.level*2)   
        
    def write(self,inStr):
        self.writer.write(self.indent+inStr+"\n")
            
    def getChartName(self,inCode):
        return "chart"+inCode
            
    def writeRecord(self,inCode,inParentCode,inName,inType,inUserType):
        self.write('<record id="' + self.getChartName(inCode) + '" model="account.account.template">')
        self.enter()
        self.write('<field name="code">'+inCode+'</field>')       
        self.write('<field name="name">'+inName+'</field>')
        self.write('<field name="reconcile" eval="False"/>')
        
        if not inParentCode and inCode != "BASE":
            inParentCode="BASE"
        
        if inParentCode:
            self.write('<field name="parent_id" ref="'+self.getChartName(inParentCode)+'"/>')
            
        self.write('<field name="type">'+inType+'</field>')
        self.write('<field name="user_type" ref="'+inUserType+'"/>')     
        
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
 
    
    
    w = XmlWriter("../account_chart.xml")    
    w.startDocument()
    
    
    cr.execute("SELECT a.code, a.name, a.type, t.code, p.code parent" 
               " FROM account_account a " 
               " LEFT JOIN account_account p ON p.id = a.parent_id "
               " LEFT JOIN account_account_type t ON t.id = a.user_type "
               " WHERE a.company_id = 1 AND NOT a.id = 1 AND a.code LIKE 'V%' "
               " ORDER BY a.code  ")
    
    for r in cr.fetchall():
        code = r[0]
        name = r[1]
        atype = r[2]
        user_type = r[3]
        parent_code = r[4]
        w.writeRecord(code,parent_code,name,atype,"account.data_account_type_%s" % (user_type,))
    
       
    cr.execute("SELECT a.code, a.name, a.type, t.code, p.code parent" 
               " FROM account_account a " 
               " LEFT JOIN account_account p ON p.id = a.parent_id "
               " LEFT JOIN account_account_type t ON t.id = a.user_type "
               " WHERE a.company_id = 1 AND NOT a.id = 1 " 
               "   AND NOT a.code LIKE 'V%' "
               "   AND ( length(a.code) != 6 OR "
               "   ( NOT ( a.code >= '200000' AND a.code < '2999999'  AND a.code != '200999' )"
               "   AND NOT ( a.code >= '300000' AND a.code < '399999' AND a.code != '300999' ) ) )"
               " ORDER BY a.code  ")
    
    for r in cr.fetchall():
        code = r[0]
        name = r[1]
        atype = r[2]
        user_type = r[3]
        parent_code = r[4]
        w.writeRecord(code,parent_code,name,atype,"account.data_account_type_%s" % (user_type,))
     
    w.endDocument()   
    w.close()   
    

if __name__ == '__main__':
    main()