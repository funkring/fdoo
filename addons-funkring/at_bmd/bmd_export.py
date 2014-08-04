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

from openerp.osv import fields,osv
from openerp.addons.at_base import util
import base64

class bmd_export(osv.osv):
        
    def _create_or_replace_attachment(self,cr,uid,oid,name,file_name,data=None,datas=None,context=None):
        attachment_obj = self.pool.get('ir.attachment')
        attachment_id = attachment_obj.search_id(cr, uid, [("datas_fname","=",file_name),("res_model","=","bmd.export"),("res_id","=",oid)])
        vals = {   "name": name,
                   "datas": data and base64.encodestring(data) or datas,
                   "datas_fname": file_name,
                   "res_model" : "bmd.export",
                   "res_id" : oid }
        
        if attachment_id:            
            attachment_obj.write(cr, uid, attachment_id, vals, context=context)
            return attachment_id
        else:
            return attachment_obj.create(cr, uid, vals, context=context)        
        
    def action_export(self,cr, uid, ids, context=None):
        if not context:
            context={}
        bmd_export_context = dict(context)
        bmd_export_context["data"]={
               "model" : "bmd.export",
               "id" : ids[0]
        }
        ir_obj = self.pool.get("ir.model.data")
        wizard_view_id = ir_obj.get_object_reference(cr, uid, 'at_bmd', 'view_bmd_export_result')[1]
        return {
               "name": "Export",
               "type": "ir.actions.act_window",
               "view_type": "form",
               "view_mode": "form",
               "res_model": "bmd.export_result",
               "view_id": wizard_view_id,
               "target": "new",
               "context": bmd_export_context,
        }       
        
    def action_export_sent(self, cr, uid, ids, context):
        if not context:
            context = {}
        
        invoice_obj = self.pool.get("account.invoice")
        account_voucher_obj = self.pool.get("account.voucher")
        account_bank_statement_obj = self.pool.get("account.bank.statement")
        account_journal_obj = self.pool.get("account.journal")
        bmd_export_obj = self.pool.get("bmd.export")
        bmd_export_result_obj = self.pool.get("bmd.export_result")
        report_obj = self.pool.get("ir.actions.report.xml")
        ir_obj = self.pool.get("ir.model.data")
        log_obj = self.pool.get("log.temp")
                   
        for bmd_export in bmd_export_obj.browse(cr, uid, ids, context):                    
            period = bmd_export.period_id
            company = bmd_export.period_id.company_id
            profile = bmd_export.profile_id
            
            period_name = period.name
            export_name = bmd_export.name
            
            bmd_export_result_id = None  
            attachment_ids = []
                                       
            bmd_export_context = context.copy()
            bmd_export_context["data"]={
                "model" : "bmd.export",
                "id" : bmd_export.id
            }                    
            bmd_export_result_id = bmd_export_result_obj.create(cr,uid,{},bmd_export_context)
            bmd_export_result = bmd_export_result_obj.browse(cr,uid,bmd_export_result_id)
            log_ids = bmd_export_result.log_ids or []
            
            #attach stammdaten
            attachment_ids.append(self._create_or_replace_attachment(cr,uid,bmd_export.id,"stamerf","stamerf",datas=bmd_export_result.stamerf,context=context))
            #attach booking file        
            attachment_ids.append(self._create_or_replace_attachment(cr,uid,bmd_export.id,"buerf","buerf",datas=bmd_export_result.buerf,context=context))
            
            def add_report(name,report_name,report_model,object_ids,add_attach=False):
                report = report_obj._lookup_report(cr,report_name)
                if report and object_ids:
                    report_context = context.copy()
                    report_context["report_title"]=name
                    report_context["add_pdf_attachments"]=add_attach
                    (report_data,ext) = report.create(cr,uid,object_ids,{"model":report_model}, report_context)
                    file_name = "%s.%s" % (util.cleanFileName(name),ext)
                    attachment_ids.append(self._create_or_replace_attachment(cr,uid,bmd_export.id,file_name,file_name,report_data,context=context))
                                                     
            # attach statement report
            if profile.send_affected_statements:
                cr.execute("SELECT s.date, s.name, l.statement_id FROM bmd_export_line bl "
                           " INNER JOIN account_move_line l ON l.id = bl.move_line_id "
                           " INNER JOIN account_bank_statement s ON s.id = l.statement_id AND s.state = 'confirm' "
                           " WHERE bl.bmd_export_id = %s "
                           " GROUP BY 1,2,3 "
                           " ORDER BY 1,2,3", (bmd_export.id,))
                
                statement_ids = [r[2] for r in cr.fetchall()]
                add_report("Auszüge %s" % (export_name,),
                           "account.bank.statement",
                           "account.bank.statement",
                           statement_ids,add_attach=True)
                
            if profile.send_statements:
                for journal in account_journal_obj.browse(cr,uid,
                                                    account_journal_obj.search(cr,uid,[("company_id","=",company.id)]),
                                                    context=context):
                    
                    statement_ids = account_bank_statement_obj.search(cr,uid,[("period_id","=",period.id),("journal_id","=",journal.id),("state","=","confirm")])
                    add_report("Auszüge %s %s" % (journal.name,export_name),
                               "account.bank.statement",
                               "account.bank.statement",
                               statement_ids,
                               add_attach=True)
                    
                                      
            # attach balance report
            if profile.send_balance_list:
                cr.execute("SELECT a.code, t.account_id FROM ("
                           " SELECT bl1.account_id AS account_id FROM bmd_export_line bl1 WHERE bl1.bmd_export_id = %s "
                           " UNION ALL " 
                           " SELECT bl2.account_contra_id AS account_id FROM bmd_export_line bl2 WHERE bl2.bmd_export_id = %s "
                           " ) t " 
                           " INNER JOIN account_account a ON a.id = t.account_id "
                           " GROUP BY 1,2 "
                           " ORDER BY 1,2 "
                           ,   (bmd_export.id,bmd_export.id) )
                
                account_ids = [r[1] for r in cr.fetchall()]
                add_report("Saldenliste %s" % (export_name,),
                           "account.balance.list",
                           "account.account",
                           account_ids)
                                            
                    
            # attach voucher list
            if profile.send_voucher_list:                            
                voucher_ids = account_voucher_obj.search(cr,uid,[("period_id","=",period.id)],order="date",context=context)
                add_report("Zahlungsübersicht %s" % (period_name,),
                           "account.voucher.list",
                           "account.voucher",
                           voucher_ids)
                                                
            # attach open invoice list
            if profile.send_open_invoice_list:                      
                open_invoice_types = [("in_invoice","Offene Eingangsrechnungen"),("out_invoice","Offene Ausgangsrechnungen")]
                
                for inv_type, inv_desc in open_invoice_types:
                    cr.execute("SELECT t.date_invoice, t.id FROM ( "
                               " SELECT inv.date_invoice AS date_invoice, inv.id AS id FROM account_invoice inv  "
                               "   INNER JOIN account_period p ON p.id = inv.period_id AND p.date_start <= %s "
                               "   WHERE inv.company_id = %s AND inv.state = 'open' AND inv.type = %s "
                               " UNION ALL "
                               " SELECT inv.date_invoice AS date_invoice, inv.id AS id FROM account_invoice inv "
                               "  INNER JOIN account_move_line ml ON ml.move_id = inv.move_id "
                               "  INNER JOIN account_move_reconcile r ON r.id = ml.reconcile_id "
                               "  INNER JOIN account_period p ON p.id = inv.period_id AND p.date_start <= %s "
                               "  WHERE inv.company_id = %s AND inv.state = 'paid' AND inv.type = %s AND r.create_date > %s "
                               " ) t GROUP BY 1,2 ORDER BY 1 ", (period.date_start,
                                                                 company.id,
                                                                 inv_type,
                                                                 period.date_start,
                                                                 company.id,
                                                                 inv_type,
                                                                 period.date_stop))
                    #
                    open_invoice_ids = [r[1] for r in cr.fetchall()]
                    add_report("%s %s" % (inv_desc,period_name),
                               "account.invoice.list",
                               "account.invoice",
                               open_invoice_ids)
                                         
            #attach invoice list
            invoice_reports = []
            if profile.send_invoice_list:
                invoice_reports.append(("account.invoice.list", 
                                       [("Liste Ausgangsrechnungen","out_invoice"),
                                        ("Liste Eingangsrechnungen","in_invoice"),
                                        ("Liste Kundengutschriften","out_refund"),
                                        ("Liste Lieferantengutschriften","in_refund")]))
            if profile.send_invoices:
                invoice_reports.append(("account.invoice",
                                       [("Ausgangsrechnungen","out_invoice"),
                                        ("Eingangsrechnungen","in_invoice"),
                                        ("Kundengutschriften","out_refund"),
                                        ("Lieferantengutschriften","in_refund")]))
                
            for invoice_report, invoice_types in invoice_reports:
                for invoice_name, invoice_type in invoice_types:
                    invoice_ids = invoice_obj.search(cr,uid,[("period_id","=",period.id),("type","=",invoice_type),
                                                          ("state","!=","draft"),("state","!=","cancel")],
                                                  order="date_invoice")
                    
                    if invoice_type in ("in_invoice","in_refund"):
                        valid_ids = []
                        for invoice_id in invoice_ids:
                            if report_obj.get_attachment_id(cr, uid, "account.invoice", invoice_id):
                                valid_ids.append(invoice_id)
                            else:
                                invoice = invoice_obj.browse(cr,uid,invoice_id,context=context)
                                log_ids.append(log_obj.warn(cr,uid,"Rechnung %s [%s] ohne Beleg" % (invoice.number, invoice_id)))
                                
                        invoice_ids = valid_ids
                                                
                    add_report("%s %s" % (invoice_name,period_name),
                               invoice_report,
                               "account.invoice",
                               invoice_ids)
            
            # check if there are warnings
            warnings = []
            if log_ids:
                #return self.pool.get("log.temp.wizard").show_logs(cr,uid,log_ids,context)
                for log in log_obj.browse(cr,uid,log_ids,context=context):
                    if not warnings:
                        warnings.append("")
                        warnings.append("Warnungen")
                        warnings.append("~~~~~~~~~")
                        warnings.append("")
                    warnings.append(log.name)
                
                                                        
            #prepare mail  
            try:
                compose_form_id = ir_obj.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            mail_context = dict(context)
            mail_context.update({
                "default_body" : "<br>".join(warnings),
                "default_model": "bmd.export",
                "default_res_id": bmd_export.id,
                "default_composition_mode": "comment",
                "default_attachment_ids" : attachment_ids
                })
            return {
                "name": "Daten Übermittlung",
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "mail.compose.message",
                "views": [(compose_form_id, "form")],
                "view_id": compose_form_id,
                "target": "new",
                "context": mail_context,
            }       

        return True
                
        
    _name = "bmd.export"
    _inherit = ["mail.thread"]
    _description = "BMD Export"
    _columns = {
        "name" : fields.char("Name",size=64,required=True,select=True),
        "period_id" : fields.many2one("account.period", "Periode",required=True,select=True),
        "profile_id" : fields.many2one("bmd.export.profile", "Profil", ondelete="restrict", required=True),
        "line_ids" : fields.one2many("bmd.export_line","bmd_export_id","BMD Export Zeilen")
    }  


class bmd_move_line_template(osv.AbstractModel):
    _name="bmd.move_line_template"
    _description="BMD Move Line Template"
    _columns = {
        "satzart" : fields.selection([("0","FIBU-Buchungssatz"),("2","Mehrzeiliger Buchungstext"),("6","Personenstammdaten")],"Satzart",size=1),
        "konto" : fields.char("Konto",size=32),
        "buchdat" : fields.date("Buchnungsdatum"),
        "gkto" : fields.char("Gegenkonto",size=9),
        "belegnr" : fields.char("Belegnummer",size=9),
        "belegdat" : fields.date("Belegdatum"),
        "kost" : fields.char("Kostenstelle",size=9),
        "kotraeger" : fields.integer("Kostenträger",size=9),
        "komenge" : fields.float("Kosten-Menge"),
        "komengenr" : fields.char("Kosten-Menge-Kz",size=4),
        "kovariator" : fields.float("Kosten-Variator"),
        "koperiode" : fields.date("Kosten-Periode"),
        "mwst" : fields.integer("Steuerprozentsatz"),
        "steuer" : fields.float("Steuer"),
        "steucod" : fields.selection([
                        ("00","Vorsteuer oder keine Steuer"),
                        ("01","Ist-Umsatzsteuer"),
                        ("03","Soll-Umsatzsteuer (= normale Umsatzsteuer)"),
                        ("07","innergemeinschaftliche Lieferung"),
                        ("08","Einkauf innergem. Erwerb, wenn kein VSt-Abzug besteht"),
                        ("09","Einkauf innergem. Erwerb, wenn VSt-Abzug besteht"),
                        ("17","steuerfreie Bauleistung (Erlös)"),
                        ("18","Reverse Charge ohne Vorsteuer"),
                        ("19","Reverse Charge mit Vorsteuer"),
                        ("28","Einkauf Bausteuer ohne Vorsteuer"),
                        ("29","Einkauf Bausteuer normal mit Vorsteuer"),
                        ("48","Aufwand §19/1b ohne VSt-Abzug"),
                        ("49","Aufwand §19/1b mit VSt-Abzug"),
                        ("57","Umsätze §19/1c+d"),
                        ("58","Aufwand §19/d ohne VSt-Abzug"),
                        ("59","Aufwand §19/d mit VSt-Abzug"),
                        ("68","Aufwand §19/1c ohne VSt-Abzug"),
                        ("69","Aufwand §19/1c mit VSt-Abzug"),
                        ("77","Erträge sonstige Leistungen EU"),
                        ("78","Aufwände Son.Leistungen EU ohne VSt-Abzug"),
                        ("79","Aufwände Son.Leistungen EU mit VSt-Abzug")
                    ],"Steuer Code",size=2),
        "bucod" : fields.selection([("1","Soll-Buchung"),("2","Haben-Buchung")],"Soll/Haben",size=1),        
        "betrag" : fields.float("Betrag"),
        "ebkennz" : fields.selection([("1","Eingangsbeleg")],"Beleg Kennzeichen",size=1),
        "skonto" : fields.float("Skonto"),
        "opbetrag" : fields.float("OP-Betrag",help="Offene Posten - Betrag"),
        "periode" : fields.date("Periode"),       
        "text" : fields.char("Buchungstext",size=72),
        "symbol" :  fields.char("Symbol",size=2),
        "extbelegnr" : fields.char("Externe Belegnummer",size=12),
        "zziel" : fields.integer("Zahlungsziel",help="Zahlungsziel in Tagen"),
        "menge" : fields.float("Menge"),
        "gegenbuchkz" : fields.selection([
                                ("E","Einzelbuchung"),
                                ("S","Sammelbuchung"),
                                ("O","Ohne Gegenbuchung")],
                                "Gegenbuchungskennzeichen",size=1),
        "verbuchkz" : fields.selection([
                        ("A","Verbuchung mit PR08A"),
                        ("P","Sammelbuchungen durch BMD")],
                        "Verbuchungskennzeichen",size=1),
        "bereich" : fields.selection([
                        ("I","Inland"),
                        ("EU","EU Ausland"),
                        ("D","Drittland"),
                        ("A","Ausland")],
                        "Bereich",size=2)
    }
    _order = "belegnr"


class bmd_export_line(osv.Model):
    _name="bmd.export_line"
    _inherit="bmd.move_line_template"
    _description="BMD Export Line"
    _columns = {        
        "bmd_export_id" : fields.many2one("bmd.export","BMD Export"),        
        "move_line_id" : fields.many2one("account.move.line", "Buchungszeile"),
        "invoice_id" : fields.many2one("account.invoice","Rechnung"),
        "partner_id" : fields.many2one("res.partner","Partner"),
        "account_id" : fields.many2one("account.account","Konto"),
        "account_contra_id" : fields.many2one("account.account","Gegenkonto")
    }
    _order = "belegnr"


class bmd_export_profile(osv.Model):
    _name = "bmd.export.profile"
    _columns = {
        "name" : fields.char("Name", size=32, required=True),
        "active" : fields.boolean("Aktiv"),
        "partner_name_as_matchcode" : fields.boolean("Partner Name als Matchcode"),
        "cession_code" : fields.char("Zession Code", size=32),        
        "export_asset_accounts" : fields.boolean("Sachkonten Exportieren"),
        "receipt_primary" : fields.boolean("Erlöskonto Buchungen"),
        "send_affected_statements" : fields.boolean("Sende betroffene Auszüge"),
        "send_statements" : fields.boolean("Sende alle Auszüge"),
        "send_balance_list" : fields.boolean("Sende Kontensalden"),
        "send_voucher_list" : fields.boolean("Sende Zahlungen"),
        "send_open_invoice_list" : fields.boolean("Sende Liste mit offenen Rechnungen"),
        "send_invoice_list" : fields.boolean("Sende Rechnung/Gutschriftenliste"),
        "send_invoices" : fields.boolean("Sende Rechnungen/Gutschriften"),
        "journal_ids" :fields.many2many("account.journal", "bmd_export_profile_journal_rel", "profile_id", "journal_id",string="Journals")
    }
    _defaults = {
        "active" : True
    }
    _order = "name"
