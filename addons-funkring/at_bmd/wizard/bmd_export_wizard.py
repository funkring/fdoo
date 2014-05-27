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

from openerp.osv import fields,osv
from openerp.addons.at_base import util
import StringIO
import base64
import re
from openerp.tools import ustr
from openerp.tools.translate import _

BLEGNR_PATTERNS =  [re.compile("^.*[^0-9]([0-9]+)$"),
                    re.compile("^([0-9]+)$")]


class bmd_export_param(osv.TransientModel):       
    
    def belegnr_get(self,value):
        if value:
            value = value.replace("/","")
            for belegNrPattern in BLEGNR_PATTERNS:
                result = belegNrPattern.match(value)
                if result:
                    return result.group(1)
        return None        
       
    def config_export(self, cr, uid, ids, context=None):
        if not context:
            context = {}
             
        export_name = ""
        tax_obj = self.pool.get("account.tax")
        journal_obj = self.pool.get("account.journal")
        invoice_obj = self.pool.get("account.invoice")
        move_obj = self.pool.get("account.move")
        account_obj = self.pool.get("account.account")
        fpos_obj = self.pool.get("account.fiscal.position")
        log_obj = self.pool.get("log.temp")
        
        for obj in self.browse(cr, uid, ids, context):
            journal_ids = [x.id for x in obj.profile_id.journal_ids]   
            if not journal_ids:
                raise osv.except_osv("Fehler!","Es wurde kein Journal ausgewählt")
                
            export_name = obj.name
            period_id = obj.period_id.id 
            profile_id = obj.profile_id.id
            receipt_primary = obj.profile_id.receipt_primary      
            export_lines = []
            log_ids = []
            
            #
            # Helper Class BmdAccountData 
            #
            class BmdAccountData:
                def __init__(self,account_code,tax,steucod,amount=0.0,amount_tax=0.0):                                           
                    self.code=account_code                    
                    self.tax=tax
                    self.steucod = steucod
                    self.amount=amount
                    self.amount_tax=amount_tax                                     
            
            def exportInvoice(invoice):                      
                company = invoice.company_id            
                account_payable = invoice.partner_id.property_account_payable
                account_receivable = invoice.partner_id.property_account_receivable   
                country = invoice.partner_id.country_id
                country_code = country and country.code or ""
                foreigner = country_code and "AT" != country.code
                european_union = False
                if foreigner and invoice.partner_id.vat:
                    european_union = True   
                                
                area = "I"
                if foreigner:
                    if european_union:
                        area = "EU"
                    elif invoice.type in ["out_invoice","out_refund"]:
                        area = "A"
                    else:
                        area="D"
                
                bmd_text = [invoice.number]             
                if invoice.name:
                    bmd_text.append(invoice.name)                
                             
                bmd_line = {
                    "bereich" : area,
                    "satzart" : "0",   
                    "invoice_id" : invoice.id,
                    "partner_id" : invoice.partner_id.id,
                    "buchdat" : invoice.date_invoice,
                    "belegdat" : invoice.date_invoice,
                    "belegnr" : self.belegnr_get(invoice.number),
                    "bucod" : "1",      
                    "zziel" : "0",
                    "text" : ":".join(bmd_text),
                    "gegenbuchkz" : "E",
                    "verbuchkz" : "A",
                    "symbol" : (invoice.journal_id and invoice.journal_id.code) or ""
                }    
                                                                              
                sign=1.0        
                if invoice.type == "out_refund":
                    sign=-1.0                    
                
                if invoice.type in ("in_refund","in_invoice"):
                    if ( invoice.type == "in_invoice"):
                        sign=-1                                            
                    bmd_line["bucod"]="2"                    
                    bmd_line["ebkennz"]="1"
                    bmd_line["konto"]= account_payable and account_payable.code or ""
                else:
                    bmd_line["konto"]= account_receivable and account_receivable.code or ""
                               
                if invoice.date_due and invoice.date_invoice:
                    bmd_line["zziel"] = (util.strToDate(invoice.date_due)-util.strToDate(invoice.date_invoice)).days
                                    
                accounts = {}                
                for line in invoice.invoice_line:
                    account = line.account_id
                    taxes = line.invoice_line_tax_id                   
                    product = line.product_id    
                    steucod = ""
                                                            
                    # Eingangs- bzw. Lieferanten Rechnungen
                    if invoice.type in ["in_invoice","in_refund"]:
                        # Für Produkt Eingang/Import werden die lokalen Steuern des Produkt/Mapping verwendet                    
                        if foreigner:
                            if product:
                                taxes = line.product_tax_ids
                            # Wenn kein Produkt angegeben wurde, wird ein reverse mapping der Steuer versucht
                            # falls ein Steuermapping verwendet wird
                            elif invoice.fiscal_position:
                                taxes = fpos_obj.unmap_tax(cr,uid,invoice.fiscal_position,taxes)
                        
                        if european_union:
                            steucod="09" #Einkauf innergem. Erwerb, wenn VSt-Abzug besteht
                            
                        if product:                        
                            if european_union and product.type=="service":
                                steucod = "19" #Reverse Charge mit Vorsteuer"
                    # Ausgangs- bzw. Rechnungen an Kunden
                    elif invoice.type in ["out_invoice","out_refund"]:
                        if european_union:
                            steucod = "07" #Innergemeinschaftliche Lieferung
                                                                         
                        
                                      
                    tax = taxes and int(taxes[0].amount*100) or 0        
                    account_key = (account.code,tax,steucod)
                    account_data = accounts.get(account_key)
                    if not account_data:
                        account_data = BmdAccountData(account.code,tax,steucod)                       
                        accounts[account_key]=account_data           
                             
                    line_total = tax_obj.compute_all(cr, uid, taxes, line.price_unit * (1-(line.discount or 0.0)/100.0), 
                                        line.quantity, product=line.product_id.id, partner=line.invoice_id.partner_id.id)  
                    
                                        
                    line_sum = line.price_subtotal_taxed
                    line_tax = line_total["total_included"]-line_total["total"]    
                               
                    account_data.amount+=line_sum
                    account_data.amount_tax+=line_tax
                                              
                                               
                def addExportLine(account_data):
                    bmd_line_copy = bmd_line.copy()
                    bmd_line_copy["gkto"]=account_data.code
                    bmd_line_copy["betrag"]=account_data.amount*sign
                    bmd_line_copy["mwst"]=account_data.tax
                    bmd_line_copy["steuer"]=round((-1.0*sign)*account_data.amount_tax,2)     
                                        
                    if account_data.steucod:
                        bmd_line_copy["steucod"]=account_data.steucod
                    
                    if receipt_primary:
                        if bmd_line_copy["bucod"]=="1":
                            bmd_line_copy["bucod"]="2"
                        if bmd_line_copy["bucod"]=="2":
                            bmd_line_copy["bucod"]="1"                            
                        tmp=bmd_line_copy["konto"]
                        bmd_line_copy["konto"]=bmd_line_copy["gkto"]
                        bmd_line_copy["gkto"]=tmp   
                        bmd_line_copy["betrag"]=bmd_line_copy["betrag"]*-1.0
                        bmd_line_copy["steuer"]=bmd_line_copy["steuer"]*-1.0
                        
                    # Steuern auf Null setzen wenn Drittland
                    if area == "D":
                        bmd_line_copy["mwst"]=0
                        bmd_line_copy["steuer"]=0.0       
                 
                    #
                    bmd_line_copy["account_id"]=account_obj.search_id(cr,uid,[("company_id","=",company.id),("code","=",bmd_line_copy["konto"])])              
                    bmd_line_copy["account_contra_id"]=account_obj.search_id(cr,uid,[("company_id","=",company.id),("code","=",bmd_line_copy["gkto"])])
                    export_lines.append((0,0,bmd_line_copy))    
                                    
                for account_data in accounts.values():  
                    addExportLine(account_data)    
                
                
            def exportMove(move):
                #
                move_lines = move.line_id
                group_credit = 0.0
                group_debit = 0.0
                group_lines = []
                group = [group_lines]
                #
                # group lines 
                for line in move_lines:
                    group_lines.append(line)                                 
                    if line.credit:                        
                        group_credit += line.credit                        
                    else:
                        group_debit += line.debit
                    # group if balanced     
                    if group_credit == group_debit and group_debit > 0:
                        group_lines = []
                        group.append(group_lines)
                
                #
                for group_lines in group:
                    debit = []
                    credit = []
                    reconcile_ids = []
                    partner = None
                    #
                    for line in group_lines: 
                        if not partner:
                            partner = line.partner_id    
                        #               
                        if line.credit:                            
                            credit.append( { "line" : line,
                                             "amount" : line.credit 
                                            } )
                        else:                            
                            debit.append( { "line" : line, 
                                            "amount" : line.debit
                                           })
                        #
                        reconcile_id = line.reconcile_id or line.reconcile_partial_id or None
                        if reconcile_id:
                            reconcile_ids.append(reconcile_id.id)
                        
                               
                    #                       
                    if not debit or not credit:
                        continue       
                    #                                
                    invoice = None
                    if reconcile_ids:
                        cr.execute("SELECT inv.id FROM account_invoice inv " 
                                   " INNER JOIN account_move_line l ON l.move_id = inv.move_id " 
                                   " INNER JOIN account_move_reconcile r ON (r.id IN %s) AND (r.id = l.reconcile_id OR r.id = l.reconcile_partial_id) "
                                   " GROUP BY 1 ", (tuple(reconcile_ids),) )
                        
                        invoice_ids = [r[0] for r in cr.fetchall()]
                        invoice = invoice_ids and invoice_obj.browse(cr,uid,invoice_ids[0],context=context) or None
                        #
                        if not partner:
                            partner = invoice.partner_id            
                    #
                    bucod = None
                    main = None
                    lines = None
                    sign = 1.0
                    #
                    if len(debit)==1 and not (len(credit)==1 and credit[0]["line"].name == "/"):
                        bucod = "1"
                        main = debit[0]
                        lines = credit
                    elif len(credit)==1:
                        bucod = "2"
                        sign = -1.0
                        main = credit[0]
                        lines = debit                    
                    else:
                        log_ids.append(log_obj.warn(cr,uid,"Buchung %s kann nicht exportiert werden (mehr als eine Haben oder Soll Buchung)" % move.name,context=context))
                        raise osv.except_osv("Fehler !","Buchung %s kann nicht exportiert werden (mehr als eine Haben oder Soll Buchung)" % move.name)
                    #
                    line = main["line"]
                    bmd_line_pattern = {
                        "satzart" : "0",
                        "partner_id" : partner and partner.id or None,
                        "konto" : line.account_id.code,
                        "account_id" : line.account_id.id,
                        "buchdat" : move.date,                    
                        "belegdat" : move.date,
                        "belegnr" : self.belegnr_get(move.name),
                        "bucod" : bucod,
                        "mwst" : 0,
                        "steuer" : 0.0,
                        "symbol" : journal and journal.code or "", 
                        "gegenbuchkz" : "E",
                        "verbuchkz" : "A",
                        "kost" : invoice and self.belegnr_get(invoice.number) or None,
                        "invoice_id" : invoice and invoice.id or None,
                        "zziel" : "0"
                    }
                    #
                    for line_data in lines:
                        line = line_data["line"]
                        bmd_line = bmd_line_pattern.copy()
                        bmd_line["betrag"]=(line_data["amount"]*sign)
                        bmd_line["text"]=line.name
                        bmd_line["gkto"]=line.account_id.code
                        bmd_line["account_contra_id"]=line.account_id.id
                        bmd_line["move_line_id"]=line.id
                        export_lines.append((0,0,bmd_line))  
                #
                return True
            
            if period_id and journal_ids:              
                for journal in journal_obj.browse(cr,uid,journal_ids,context=context):
                    if journal.type in ("sale","sale_refund","purchase","purchase_refund"):
                        invoice_ids = invoice_obj.search(cr,uid,[("period_id","=",period_id),("journal_id","=",journal.id),("state","in",("open","paid"))])
                        for invoice in invoice_obj.browse(cr,uid,invoice_ids):
                            exportInvoice(invoice)                        
                    elif journal.type in ("bank","cash"):
                        move_ids = move_obj.search(cr, uid, [("period_id","=",period_id),("journal_id","=",journal.id),("state","=","posted")], context=context)
                        for move in move_obj.browse(cr,uid,move_ids,context=context):
                            exportMove(move)
                                                  
            
            bmd_export_obj = self.pool.get("bmd.export")          
            vals = bmd_export_obj.default_get(cr, uid, bmd_export_obj.fields_get_keys(cr,uid,context), context)
            vals["period_id"]=period_id       
            vals["line_ids"]=export_lines
            vals["name"]=export_name   
            vals["profile_id"] = profile_id
            bmd_export_id = bmd_export_obj.create(cr,uid,vals,context)
                               
            res_obj = self.pool.get("ir.model.data")
            res_id = res_obj.get_object_reference(cr,uid,"at_bmd","view_bmd_export_form")[1]                                
            return {
                "name" : "BMD Export",
                "view_type" : "form",
                "view_mode" : "form",
                "res_model" : "bmd.export",      
                "res_id" : bmd_export_id,          
                "view_id" : False,
                "views" : [(res_id,"form")],
                "type" : "ir.actions.act_window",
                "context" : { "period_id" :  obj.period_id.id,
                              "journal_ids" : journal_ids,
                              "default_log_ids" : log_ids
                            }
            }
                    
        return {"type" : "ir.actions.act_window_close"}
    
    def _default_profile_id(self, cr, uid, context=None):
        return self.pool.get("bmd.export.profile").search_id(cr, uid, [])
    
    def onchange_period(self, cr, uid, ids, period_id, context=None):
        res = {}
        if period_id:
            period_obj = self.pool.get("account.period")        
            period = period_obj.browse(cr, uid, period_id, context=context)
            res["value"] = {"name" : _("Transfer %s") % period.name }
        return res
            
            
    _rec_name="period_id"
    _name="bmd.export_param"
    _description="BMD Journal Export Parameters"
    _columns = {
        "profile_id" : fields.many2one("bmd.export.profile", "BMD Export Profile", required=True),
        "period_id" : fields.many2one("account.period", "Period", required=True),    
        "name" : fields.char("Name"),
        "journal_ids" :fields.many2many("account.journal", "bmd_export_param_journal_rel", "bmd_export_param_id", "journal_id",string="Journals"),            
    }   
    _defaults = {
        "profile_id" : _default_profile_id
    }
    
    
class fix_format(object):
    
    def __init__(self):
        self.line = ""
       
    def addf(self,inName,inValue,inWidth,inPre,inPost,inStart,inEnd):
        if len(self.line)+1!=inStart:
            raise osv.except_osv("Fehler !","Falsche Position bei %s: %d != %d" % (inName,len(self.line),inStart))
        tokens = str(inValue or 0.0).split(".")
        
        first  = ""
        second = ""
        if len(tokens) > 2:
            first = tokens[0]
            second = tokens[1]
        elif len(tokens):
            first = tokens[0]
        
        self.line +=first.rjust(inPre,"0")
        self.line +=second.ljust(inPost,"0")
        
        if inPre+inPost != inWidth:
            self.line +=inValue >= 0.0 and "+" or "-"
            
        if len(self.line)!=inEnd:
            raise osv.except_osv("Fehler !","Falsche Position bei %s: %d != %d" % (inName,len(self.line),inEnd))                
 
    def addn(self,inName,inValue,inWidth,inStart,inEnd):
        if len(self.line)+1!=inStart:
            raise osv.except_osv("Fehler !","Falsche Position bei %s: %d != %d" % (inName,len(self.line),inStart))
        self.line += ustr(inValue or "").rjust(inWidth,"0")[:inWidth]
        if len(self.line)!=inEnd:
            raise osv.except_osv("Fehler !","Falsche Position bei %s: %d != %d" % (inName,len(self.line),inEnd))                
        
    def adds(self,inName,inValue,inWidth,inStart,inEnd):
        if len(self.line)+1!=inStart:
            raise osv.except_osv("Fehler !","Falsche Position bei %s: %d != %d" % (inName,len(self.line),inStart))
        inValue=inValue or ""
        inValue=inValue.strip()
        self.line += ustr(inValue).ljust(inWidth," ")[:inWidth]
        if len(self.line)!=inEnd:
            raise osv.except_osv("Fehler !","Falsche Position bei %s: %d != %d" % (inName,len(self.line),inEnd))
        

class bmd_export_result(osv.TransientModel):
        
    def action_show(self, cr, uid, ids, context=None):
        for wizard in self.browse(cr, uid, ids, context=context):
            return {
                "name" : _("BMD Export"),
                "res_model" : "bmd.export",   
                "res_id" :  wizard.export_id.id,
                "type" : "ir.actions.act_window",
                "view_type" : "form",
                "view_mode" : "form"
            }
        return {}
        
    def default_get(self, cr, uid, fields_list, context=None):        
        res = super(bmd_export_result,self).default_get(cr,uid,fields_list,context)
        log_ids = res.get("log_ids") or []
        log_obj = self.pool.get("log.temp")
        
        def formatFloat(inValue):
            return ("%.2f" % inValue).replace(".",",")
        
        data = util.data_get(context)
        if not data or data["model"] != "bmd.export":
            return res
                
        partner_ids = set()
        ir_property = self.pool.get("ir.property")
        default_partner_receivable = ir_property.get(cr,uid,"property_account_receivable","res.partner")
        default_partner_payable =  ir_property.get(cr,uid,"property_account_payable","res.partner")    
        
        accounts = {}
        export_id = data["id"]
        if export_id:           
            bmd_export_obj = self.pool.get("bmd.export")
            bmd_export = bmd_export_obj.browse(cr,uid,export_id,context)
            profile = bmd_export.profile_id
            
                      
            #export belege
            output = StringIO.StringIO()
            lf = "\r\n"
            output.write("konto;buchdat;gkto;belegnr;belegdat;mwst;bucod;betrag;steuer;text;zziel;symbol;gegenbuchkz;verbuchkz;steucod;")
            output.write(lf)
            for line in bmd_export.line_ids:
                # 
                if line.account_id:
                    accounts[line.account_id.code]=line.account_id
                if line.account_contra_id:
                    accounts[line.account_contra_id.code]=line.account_contra_id
                #
                if line.partner_id:
                    partner_ids.add(line.partner_id.id)
                output.write(line.konto)
                output.write(";")
                output.write(util.dateFormat(line.buchdat,"%Y%m%d"))
                output.write(";")
                output.write(line.gkto)
                output.write(";")
                output.write(line.belegnr)
                output.write(";")
                output.write(util.dateFormat(line.belegdat,"%Y%m%d"))
                output.write(";")
                output.write(str(line.mwst))
                output.write(";")
                output.write(line.bucod)
                output.write(";")
                output.write(formatFloat(line.betrag))
                output.write(";")
                output.write(formatFloat(line.steuer))
                output.write(";")
                output.write(line.text)
                output.write(";")                
                output.write(str(line.zziel))
                output.write(";")
                output.write(line.symbol)
                output.write(";")
                output.write(line.gegenbuchkz)
                output.write(";")
                output.write(line.verbuchkz)
                output.write(";")
                if line.steucod:
                    output.write(line.steucod)
                output.write(";")                
                output.write(lf)
            res["buerf"] = base64.encodestring(output.getvalue().encode("cp1252"))
            output.close()
            
            #export stammdaten
            output = StringIO.StringIO()
            def logw(message):
                log_ids.append(log_obj.warn(cr,uid,message))
                       
            for partner in self.pool.get("res.partner").browse(cr,uid,list(partner_ids),context):
                partner_account_codes = []
                payable_account = partner.property_account_payable
                receivable_account = partner.property_account_receivable
                #                
                if payable_account and payable_account.code and len(payable_account.code) > 4:
                    if not default_partner_payable or default_partner_payable.id != payable_account.id:                    
                        partner_account_codes.append(payable_account.code)                                                
                        accounts.pop(payable_account.code,None) #remove from accounts
                if receivable_account and receivable_account.code and len(receivable_account.code) > 4:
                    if not default_partner_receivable or default_partner_receivable.id != receivable_account.id:
                        partner_account_codes.append(receivable_account.code)
                        accounts.pop(receivable_account.code,None) #remove from accounts
                #
                cession_code = None
                if partner.customer:
                    cession_code = profile.cession_code
                #
                if profile.partner_name_as_matchcode:
                    matchcode = partner.name
                else:
                    matchcode = partner.ref
                #
                for account_code in partner_account_codes:
                    f = fix_format()
                    country = partner.country_id
                    if not country:                        
                        logw("Kein Land für Partner %s gesetzt!" % partner.name)
                    country_code = country and country.code and country.code or ""                  
                    foreigner = country_code and "AT" != country.code
                    discount_days = 0
                    discount_percent = 0.0
                    payment_days = 0
                    
                    payment_term = partner.property_payment_term
                    if payment_term:
                        payment_lines = payment_term.line_ids
                        if payment_lines:                            
                            payment_line_first = payment_lines[0]
                            payment_line_last = payment_lines[-1]
                            payment_days=payment_line_last.days
                            if payment_line_first.value=="procent":
                                discount_percent=payment_line_first.value_amount*100.0
                                if payment_line_first != payment_line_last:
                                    discount_days = payment_line_first.days
                            
                    
#                    inv_account=receivable_account
#                    if account==receivable_account:
#                        inv_account=payable_account
                    
                    f.addn("1-kontonummer",account_code or "",9,1,9)                      
                    f.adds("4-name",partner.name or "",35,10,44)
                    f.adds("5-matchcode",matchcode or "",20,45,64)               
                    f.adds("11-titel",partner.title and partner.title.name or "",15,65,79)
                    f.adds("5-beruf","",35,80,114)
                    f.adds("6-strasse",partner and partner.street or "",30,115,144)
                    f.adds("7-plz",partner and partner.zip or "",12,145,156)
                    f.adds("8-ort",partner and partner.city or "",20,157,176)
                    f.adds("9-postfach","",20,177,196)
                    f.adds("10-postfach-plz","",12,197,208)
                    f.adds("59-strassenkz","",4,209,212)
                    f.adds("12-staat",(foreigner and country_code) or "",3,213,215)                        
                    f.adds("13-kontaktperson",partner.name or "",30,216,245)
                    f.adds("14-telefonnummer",partner.phone or "",18,246,263)
                    f.adds("15-telefax",partner.fax or "",18,264,281)
                    f.adds("16-email",partner.email or "",50,282,331)
                    f.adds("17-internet","",35,332,366)
                    f.adds("40-bankkonto","",20,367,386)
                    f.adds("41-blz","",12,387,398)
                    f.adds("52-iban","",34,399,432)
                    f.adds("42-swift","",12,433,444)
                    f.adds("49-bank-land","",2,445,446)
                    f.adds("18-ustid",partner.vat or "",15,447,461),
                    f.adds("53-zessionkz",cession_code,1,462,462),
                    f.addn("65-datum","",8,463,470),
                    f.addn("43-zahlsperre","",2,471,472),
                    f.addn("44-zahlspesen","",2,473,474),
                    f.addn("45-zahlgrund","",2,475,476),
                    f.addn("46-zahlumsatzpos","",4,477,480),
                    f.addn("47-zahlueberweisungsart","",2,481,482),
                    f.addn("48-zahlbank","",4,483,486),
                    f.addn("50-bankeinzug","",4,487,490),
                    f.addn("51-fremdkonto","",9,491,499),
                    f.addn("20-auslaender",(foreigner and "1") or "",2,500,501),
                    f.addn("21-keinesteuer","",2,502,503),
                    f.addn("22-zahlungsziel",payment_days,6,504,509),                    
                    f.addf("23-skonto",discount_percent,5,3,2,510,514),
                    f.addn("26-skontotage",discount_days,4,515,518),
                    f.addn("23-skonto2","",5,519,523),
                    f.addn("26-skontotage2","",4,524,527),
                    f.addn("28-kondition","",4,528,531),
                    f.addf("27-tol-proz",0.0,5,3,2,532,536),
                    f.addn("30-mahnsperre","",2,537,538),
                    f.addn("31-mahnkosten","",2,539,540),
                    f.addn("32-mahnverbuchkz","",2,541,542),
                    f.addn("33-mahndatum","",8,543,550),
                    f.addn("34-mahnformular","",4,551,554),
                    f.addn("35-mahnkontoauszug","",2,555,556)
                    f.addn("27-bonitaet","",4,557,560)
                    #f.addn("39-gegenverrechnungs-konto",inv_account and inv_account.code or "",9,561,569)
                    f.addn("39-gegenverrechnungs-konto","",9,561,569)
                    f.addn("54-divcode","",2,570,571)
                    f.addn("55-kkreis","1",2,572,573)
                    f.addn("56-sammelkonto","",9,574,582)
                    f.addn("57-rechnungskonto","",9,583,591)
                    f.addn("19-uid-datum","",8,592,599)
                    f.addn("60-firmen-anrede","",4,600,603)
                    f.addn("61-persoenl-anrede","",4,604,607)
                    f.addn("62-zu-handen-anrede","",4,608,611)
                    f.addn("63-brief-anrede","",4,612,615)
                    f.addn("66-branchenkz","",4,616,619)
                    f.addn("67-vertreter1","",6,620,625)
                    f.addn("68-vertreter2","",6,626,631)
                    f.addn("69-versandart","",4,632,635)
                    f.addn("70-verkaufsgebiet","",4,636,639)
                    f.addn("71-handelsring","",4,640,643)
                    f.addn("72-km-entf","",4,644,647)
                    f.addn("73-rabatt-code","",4,648,651)
                    f.addf("74-rabatt",0.0,9,6,2,652,660)
                    f.addf("75-auftragsstand",0.0,18,15,2,661,678)
                    f.addf("76-kreditlimit",0.0,18,15,2,679,696)
                    f.addf("77-wechselobligo",0.0,18,15,2,697,714)
                    f.addn("64-staaten-nummer","",4,715,718)
                    f.addn("79-fipkurz-zahlmodus","",2,719,720)
                    f.addn("208-varcode1","",4,721,724)
                    f.addn("206-umstkonto","",10,725,734)
                    f.addn("226-DGNR","",9,735,743)
                    f.addn("Platzhalter","",135,744,878)
                    f.addn("213-DL-Code","",4,879,882)
                    f.addn("NTCS-Kontogruppe","",1,883,883)
                    f.addn("210-Zweitwaehrung","",4,884,887)
                    f.adds("220 - Freifeld alf1","",20,888,907)
                    f.adds("221 - Freifeld alf2","",20,908,927)
                    f.adds("222 - Freifeld alf3","",1,928,928)
                    f.addf("223 - Freifeld num1",0.0,18,16,2,929,946)
                    f.addf("224 - Freifeld num2",0.0,18,15,2,947,964)
                    f.addn("225 - Freifeld num3","",4,965,968)
                    f.addn("209 - Varcode2","",9,969,977)
                    f.addn("201 - Fremdwaehrungs-Code","",4,978,981)
                    f.addn("202 - Landkennz","",4,982,985)
                    f.addn("205 - EB-Buchkonto","",9,986,994)
                    f.addn("203 - Buchsperre","",2,995,996)
                    f.addn("207 - EB-Uebernahme-Kz","",2,997,998)
                    f.addn("Loeschkz","",1,999,999)
                    f.adds("Kontrollkenzeichen","*",1,1000,1000)
                    #
                    output.write(f.line)
                    output.write(lf)   
            
            if profile.export_asset_accounts:
                for account_code, account in accounts.items():
                    f = fix_format()
                    f.addn("1-kontonummer",account_code,9,1,9)                      
                    f.adds("101-name",account.name or "",35,10,44)
                    f.adds("3-matchcode",account.name or "",20,45,64)
                    f.adds("Name 2","",35,65,99)
                    f.adds("206 - Referenzkonto","",12,100,111)
                    f.addn("105 - MWST-Code",0,4,112,115)
                    #
                    taxes = account.tax_ids
                    if taxes:
                        f.addf("106 - MWST",taxes[0].amount,5,3,2,116,120)
                    else:                    
                        f.addf("106 - MWST",0.0,5,3,2,116,120)
                    #
                    f.addn("107 - MWST-Kennzeichen",0,4,121,124)
                    f.addn("108 - USt-Rechcode",0,2,125,126)
                    f.addn("110 - KU-Code",0,4,127,130)
                    f.addf("111 - KU-Prozent",0.0,5,3,2,131,135)
                    f.addn("112 - Kostencode",0,2,136,137)
                    f.addn("113 - Kostennummer",0,9,138,146)
                    f.addn("114 - Kostenkonto",0,9,147,155)
                    f.addn("115 - Kostenart",0,4,156,159)
                    f.addn("116 - Kosten-BAB-Pos-Nr",0,4,160,163)
                    f.addf("117 - Kost-Variator",0.0,5,3,2,164,168)
                    f.addn("118 - Kost-Mengenzeichen",0,4,169,172)
                    f.addn("120 - Einheitswertkennzeichen",0,4,173,176)
                    f.addf("121 - IFB-Prozentsatz",0.0,5,3,2,177,181)
                    f.addf("122 - Nutzungsdauer",0.0,5,3,2,182,186)                                        
                    f.addn("126 - OP-Code",account.reconcile and 1 or 0,2,187,188)
                    f.addn("123 - ANBU-Erfass-Kz",0,2,189,190)
                    f.addn("127 - FP-Automatik",0,4,191,194)
                    f.addn("128 - FP-Zahlschl",0,4,195,198)
                    f.addf("129 - FP-MWST",0.0,5,3,2,199,203)
                    #
                    account_type = account.user_type
                    glz = []
                    if account_type.code == "expense":
                        glz.append("3")
                    elif account_type.code == "income":
                        glz.append("4")
                    elif account_type.code == "liability":
                        glz.append("2")
                    else:
                        glz.append("1")                                            
                    glz.append(account_code[0])
                    glz.append("00")
                    f.adds("131 - Glz Saldenliste","".join(glz),4,204,207)
                    #
                    f.addn("132 - Glz Bilanz HR",0,4,208,211)
                    f.addn("133 - Glz Bilanz RLG",0,4,212,215)
                    f.addn("134 - Glz KERF",0,4,216,219)
                    f.addn("135 - Glz Ueberschuss",0,4,220,223)
                    f.addn("136 - Glz Best. + Erfolg",0,4,224,227)
                    f.addn("137 - Glz Cash-Flow",0,4,228,231)
                    f.addn("138 - Glz Kapitalfluss",0,4,232,235)
                    f.addn("139 - Glz Geldfluss",0,4,236,239)
                    f.addn("140 - Glz Bilanzkennz",0,4,240,243)
                    f.addn("141 - Glz Insolvenz",0,4,244,247)
                    f.addn("142 - Glz Einheitswert",0,4,248,251)
                    f.addn("143 - Glz KerfGraf",0,4,252,255)
                    f.addn("144 - Glz Finplan",0,4,256,259)
                    f.addn("145 - Glz cz. Bil. lang",0,4,260,263)
                    f.addn("146 - Glz cz. Bil. kurz",0,4,264,267)
                    f.addn("147 - Glz Bilanz n. BWG",0,4,268,271)
                    f.addn("148 - Glz Kurzfr. Finp.",0,4,272,275)
                    f.addn("149 - Glz 19",0,4,276,279)
                    f.addn("150 - Glz 20",0,4,280,283)
                    f.addn("151 - Ersatzglz BilHR",0,4,284,287)
                    f.addn("152 - Ersatzglz BilRLG",0,4,288,291)
                    f.addn("153 - Ersatzglz EHW",0,4,292,295)
                    f.addn("154 - Ersatzglz Bestv",0,4,296,299)
                    f.addn("155 - Bestver.Buchkto",0,9,300,308)
                    f.addn("156 - Ezk-gesamt",0,4,309,312)
                    f.addn("157 - Ezk-fix",0,4,313,316)
                    f.addn("158 - Ezk-variabel",0,4,317,320)
                    f.addn("160 - Gemeinde",0,4,321,324)
                    f.addf("161 - VSt-Pauschale",0.0,6,3,2,325,330)
                    f.addn("162 - Getkennz",0,2,331,332)
                    f.addf("163 - Getaufschl",0.0,8,5,2,333,340)
                    f.addn("164 - Getränkesteuer-Code",0,4,341,344)
                    f.addf("165 - Getränkesteuer",0.0,6,3,2,345,350)
                    f.addf("166 - Getränkesteuer Bedienungsprozente",0.0,6,3,2,351,356)
                    f.addn("167 - Getränkesteuer Kontonummer",0,9,357,365)
                    f.addf("186 - Voranschlag",0.0,18,15,2,366,383)
                    f.addn("187 - FP-VZ-Drehung",0,2,384,385)
                    f.addn("188 - FIPKURZ-Ist-Wert",0,2,386,387)
                    f.addn("189 - FIPKURZ-VZ-Drehung",0,2,388,389)
                    f.addn("GLZ2-1 bis GLZ2-10",0,40,390,429)
                    f.addn("GLZers2-1 bis GLZers2-10",0,40,430,469)
                    f.addn("130 - Korekce",0,2,470,471)
                    f.adds("169 - Warennr","",10,472,481)
                    f.addf("122 - Dauer-hr",0.0,5,3,2,482,486)
                    f.addf("214 - Dauer-sr",0.0,5,3,2,487,491)
                    f.addf("215 - Dauer-IAS",0.0,5,3,2,492,496)
                    f.addf("216 - Afaproz-hr",0.0,5,3,2,497,501)
                    f.addf("217 - Afaproz-sr",0.0,5,3,2,502,506)
                    f.addf("218 - Afaproz-IAS",0.0,5,3,2,507,511)
                    f.addn("208 - Varcode 1",0,4,512,515)
                    f.addf("206 - Umstellungskonto",0.0,10,10,0,516,525)
                    f.addn("207 - skonto-kz",0,2,526,527)
                    f.addn("119 - Web-Kz",0,2,528,529)
                    f.addn("170 - UVA-Pauschal-%",0,5,530,534)
                    f.addn("198 - Steuerart IT",0,4,535,538)
                    f.adds("Platzhalter","",340,539,878)
                    f.addn("213 - DL-Code",0,4,879,882)
                    f.addn("NTCS-Kontogruppe",0,1,883,883)
                    f.addn("210 - Zwitwährung",0,4,884,887)
                    f.adds("220 - Freifeld alf1","",20,888,907)
                    f.adds("221 - Freifeld alf2","",20,908,927)
                    f.adds("222 - Freifeld alf3","",1,928,928)
                    f.addf("223 - Freifeld num1",0.0,18,15,2,929,946)
                    f.addf("224 - Freifeld num2",0.0,18,15,2,947,964)
                    f.addn("225 - Freifeld num3",0,4,965,968)
                    f.addn("209 - Varcode 2",0,9,969,977)
                    f.addn("201 - Fremdwärhungs-Code",0,4,978,981)
                    f.addn("202 - Landkennz",0,4,982,985)
                    f.addn("205 - EB-Buchkonto",0,9,986,994)
                    f.addn("203 - Buchsperre",account.type == "closed" and 1 or 0,2,995,996)
                    f.addn("204 - EB-Uebernahme-Kz",0,2,997,998)
                    f.addn("Loeschkz",0,1,999,999)
                    f.adds("Kontrollzeichen","*",1,1000,1000)
                    #       
                    output.write(f.line)                                                                                 
                    output.write(lf)         
                    
            res["stamerf"] = base64.encodestring(output.getvalue().encode("cp1250","replace"))
            res["export_id"]=export_id    
            res["log_ids"]=log_ids 
            output.close()
        return res
            
    _name = "bmd.export_result"
    _description = "BMD Export Files"
    _columns = {             
        "export_id" : fields.many2one("bmd.export","BMD Export"),   
        "stamerf" : fields.binary("BMD Stammdaten Export",filename="stamerf_name",readonly=True),
        "stamerf_name" : fields.char("BMD Stammdaten Export Name"),
        "buerf" : fields.binary("BMD Belege Export",filename="buerf_name",readonly=True),
        "buerf_name" : fields.char("BMD Belege Export Name"),        
        "log_ids" : fields.many2many("log.temp", string="Log",readonly=True)
    }
    _defaults =  {
        "stamerf_name" : "stamerf",
        "buerf_name" : "buerf"
    }
 