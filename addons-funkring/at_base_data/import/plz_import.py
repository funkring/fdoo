# -*- coding: UTF-8 -*-
'''
Created on 14.01.2011

@author: martin
'''
import xlrd

LAND = {
  "9" : "W",
  "8" : "VBG",
  "7" : "TIR",
  "6" : "STM",
  "5" : "SBG",
  "4" : "OOE",
  "3" : "NOE",
  "2" : "KNT",
  "1" : "BGL" 
}

if __name__ == '__main__':
    
    """ Schreibe Kontakt Daten """
        
    f = open("../data/plz.xml","w")
    indent = 0
    
    def writeln(inValue):
        for i in range(indent):
            f.write("  ")            
        f.write(inValue)
        f.write("\n")
        
    writeln('<?xml version="1.0" encoding="utf-8"?>')
    writeln('<openerp>')
    writeln('<data>')    
    indent+=1
    
    wb = xlrd.open_workbook("./gemeinden.xls")    
    sheet = wb.sheet_by_index(0)
    firstRow = True
    processedPlz = set()
    
    rowCount = sheet.nrows
    row = 5
    while row < rowCount:                
        nummer = sheet.cell(row,0)
        ort = sheet.cell(row,1)
        plz = sheet.cell(row,4)
        
        if ort and plz:
            ort = ort.value
            plz = plz.value        
            nummer = nummer.value
                        
            if plz and ort and not plz in processedPlz:
                state_code = LAND[str(nummer)[0]]
                processedPlz.add(plz)                            
                writeln('<record id="city_' + plz  + '" model="res.city">')
                indent+=1
                writeln('<field name="%s">%s</field>' % ("code", plz) )
                writeln('<field name="%s">%s</field>' % ("name", ort) )
                writeln('<field name="%s" ref="at_%s"/>' % ("state_id",state_code.lower()) )                        
                indent-=1
                writeln("</record>")
                writeln("")
                    
        row += 1
       
    indent-=1
    writeln("</data>") 
    writeln("</openerp>")
    
    f.close()
    