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
        return "tax_%s" % (re.sub("[^A-Za-z0-9]", "", inName.lower().replace("steuer","")),)
    
    def getAccountID(self,inCode):
        return "chart"+inCode
            
    def getTaxCodeID(self,inCode):
        return "tax_code_%s" % (inCode,)
            
    def writeRecord(self,name,
                    description,
                    tax_type,
                    percent,
                    invoice_account,                    
                    creditnote_account,
                    tax_base,
                    tax_base_sign,
                    tax,
                    tax_sign,
                    tax_credit_base,
                    tax_credit_base_sign,
                    tax_credit,
                    tax_credit_sign,
                    type_tax_use,
                    seq):
        
        
        self.write('<record id="' + self.getID(name) + '" model="account.tax.template">')
        self.enter()
        self.write('<field name="chart_template_id" ref="austria_chart_template"/>')
        self.write('<field name="name">%s</field>' % (name,))
        if description:
            self.write('<field name="description">%s</field>' % (description,))
        
        
        self.write('<field name="amount">%s</field>' % (percent,))
        self.write('<field name="type">%s</field>' % (tax_type,))
        
        if invoice_account:
            self.write('<field name="account_collected_id" ref="%s"/>' % (self.getAccountID(invoice_account),))
        if creditnote_account:
            self.write('<field name="account_paid_id" ref="%s"/>' % (self.getAccountID(creditnote_account),))
        if tax_base:
            self.write('<field name="base_code_id" ref="%s"/>' % (self.getTaxCodeID(tax_base),))
            self.write('<field name="base_sign">%s</field>' % (tax_base_sign,))            
        if tax:
            self.write('<field name="tax_code_id" ref="%s"/>' % (self.getTaxCodeID(tax),))
            self.write('<field name="tax_sign">%s</field>' % (tax_sign,))
        if tax_credit_base:
            self.write('<field name="ref_base_code_id" ref="%s"/>' % (self.getTaxCodeID(tax_credit_base),))
            self.write('<field name="ref_base_sign">%s</field>' % (tax_credit_base_sign,))
        if tax_credit:
            self.write('<field name="ref_tax_code_id" ref="%s"/>' % (self.getTaxCodeID(tax_credit),))
            self.write('<field name="ref_tax_sign">%s</field>' % (tax_credit_sign,))
        if type_tax_use:
            self.write('<field name="type_tax_use">%s</field>' % (type_tax_use,))
        if seq:
            self.write('<field name="sequence">%s</field>' % (seq,))
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
 
    
    
    w = XmlWriter("../account_tax.xml")    
    w.startDocument()
    
    
    cr.execute(
    " select t.name,t.description,t.type,t.amount,a1.code,a2.code, "
    " tc1.code, t.base_sign, " 
    " tc2.code, t.tax_sign, " 
    " ref_tc1.code, t.ref_base_sign, " 
    " ref_tc2.code, t.ref_tax_sign, "
    " t.type_tax_use, " 
    " t.sequence "
    " from account_tax t " 
    " left join account_account a1 on a1.id = t.account_collected_id " 
    " left join account_account a2 on a2.id = t.account_paid_id " 
    " left join account_tax_code tc1 on tc1.id = t.base_code_id " 
    " left join account_tax_code tc2 on tc2.id = t.tax_code_id " 
    " left join account_tax_code ref_tc1 on ref_tc1.id = t.ref_base_code_id " 
    " left join account_tax_code ref_tc2 on ref_tc2.id = t.ref_tax_code_id " 
    " where t.company_id=1 " )
    
    for r in cr.fetchall():
        name = r[0]
        description = r[1]
        tax_type = r[2]
        percent = r[3]
        invoice_account = r[4]
        creditnote_account = r[5]
        tax_base = r[6]
        tax_base_sign = r[7]
        tax = r[8]
        tax_sign = r[9]
        tax_credit_base = r[10]
        tax_credit_base_sign = r[11]
        tax_credit = r[12]
        tax_credit_sign = r[13]
        type_tax_use = r[14]
        seq = r[15]
        
        w.writeRecord(name,description,tax_type,percent,invoice_account,creditnote_account,
                      tax_base,tax_base_sign,
                      tax,tax_sign,
                      tax_credit_base,
                      tax_credit_base_sign,
                      tax_credit,
                      tax_credit_sign,
                      type_tax_use,
                      seq)
     
    w.endDocument()   
    w.close()   
    

if __name__ == '__main__':
    main()