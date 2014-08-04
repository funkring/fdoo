#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 21.08.2010

@author: martin
'''

import csv

from xml.sax.saxutils import escape


class XmlWriter:    
    indent=""        
    level=0
    def __init__(self,fileName):
        self.writer = open(fileName,"w")
        
    def enter(self):
        self.level+=1
        self.indent = "".rjust(self.level*2)        
        
    def exit(self):
        self.level-=1
        self.indent = "".rjust(self.level*2)   
        
    def write(self,inStr):
        self.writer.write(self.indent+inStr+"\n")
            
    def getBankName(self,inCode):
        return "bank"+inCode
            
              
    def writeField(self,inFieldName,inValue):
        if len(inValue):
            self.write('<field name="'+inFieldName+'">'+escape(inValue)+'</field>')
        
    def writeSearch(self, inModel,inFieldName, inValue):
        if len(inValue):
            self.write('<field model="' + inModel + '" name="'+inFieldName+'" search="[(\'name\',\'=\',\'' + inValue +'\')]"/>')
            
    def writeRef(self, inFieldName, inRef):
        if len(inRef):
            self.write('<field name="'+inFieldName+'" ref="'+inRef+'"/>')
            
    def writeToManyRef(self,inFieldName, inRef):
        if len(inRef):
            self.write('<field name="'+inFieldName+'" eval="[(6,0, [ref(\''+inRef+'\')])]"/>')
            
    def convert(self,inFile,inWriter,inDescription):        
        currentFile = str(inFile)
        reader = csv.reader(open(currentFile,"rb"),delimiter=';',quotechar='"')
                
        hasHeader = False
        header = []        
        convertCount = 0
        readCount = 0
        rowCount = 0
        for row in reader:
            rowCount+=1
            if rowCount < 6:
                continue
                             
            if not hasHeader: 
                hasHeader = True
                for cell in row:                    
                    header.append(cell.strip().decode("iso8859-15").encode("UTF-8"))
                    
                    
            else:
                data = {}
                i=0
                for cell in row:
                    data[header[i]]=cell.decode("iso8859-15").encode("UTF-8")
                    i+=1
                    
                readCount+=1
                if inWriter(data):
                    convertCount+=1
                    
                                
                
            
        print "Exported " + inDescription + ": " + str(convertCount) + "/" + str(readCount)
        
            
    def writeAccount(self,inData):
        bic = inData.get("SWIFT-Code") or inData["Bankleitzahl"]
        self.write('<record id="' + self.getBankName(bic) + '" model="res.bank">')
        self.enter()
        self.writeField("name", inData["Bankenname"])
        self.writeField("bic", inData["Bankleitzahl"])
        self.writeField("street",inData["Straße"])
        self.writeField("zip",inData["PLZ"])
        self.writeSearch("res.country", "country", "Austria")
        self.writeSearch("res.country.state","state",inData["Bundesland"])
        
        try:
            self.writeField("email",inData["E-MAIL"])
        except:
            pass
        
        self.writeField("phone",inData["Telefon"])
        self.writeField("fax",inData["Fax"])
        self.writeField("active","1")
        self.writeField("bic",inData["SWIFT-Code"])
        
        self.exit()
        self.write('</record>')                
        self.write('')
        return True
    
    def convertAccounts(self,inFile):
        self.convert(inFile, self.writeAccount, "Banken")
            
    def close(self):
        self.writer.close()
    

if __name__ == '__main__':
    
    w = XmlWriter("../data/banks_at.xml")    
    w.write('<?xml version="1.0" encoding="utf-8"?>')
    w.write('<openerp>')
    w.write('<data noupdate="1">')
    
    w.enter()
       
    w.convertAccounts("./kiverzeichnis_gesamt_de_1376478751742.csv")               
    
    w.exit()        
    w.write('</data>')
    w.write('</openerp>')    
    w.close()