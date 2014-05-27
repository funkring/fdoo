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
import logging

_logger = logging.getLogger(__name__)

class austrian_erp_wizard(osv.osv_memory):
      
    def execute(self, cr, uid, ids, context=None):
        return True
      
    def action_apply(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        
        seq_map = {
            ("account.analytic.account","Analytic account sequence") : ("Analytisches Konto","AA",0),            
            ("account.bank.statement","Account Bank Statement") : ("Bankauszug","BA %(year)s/%(month)s/%(day)s/",0),
            ("account.cash.statement","Account Cash Statement") : ("Kassabuch", "KB %(year)s/%(month)s/%(day)s/",0),
            ("account.reconcile","Account reconcile sequence") : ("Ausgleich", "A",0),
            ("bank_pay_voucher","Bank Payment") : ("Buchung Bankzahlung","%(year)s",3), 
            ("bank_rec_voucher","Bank Receipt") : ("Buchung Bankgutschrift","%(years)s",3),
            ("pay_voucher","Cash Payment") : ("Buchung Barauszahlung","%(years)s",3),
            ("rec_voucher","Cash Receipt") : ("Buchung Bareinzahlung","%(years)s",3),
            ("cont_voucher", "Contra Entry") : ("Buchung Gutschrift","%(years)s",3),
            ("journal_pur_vou","Purchase Entry") : ("Buchung Einkauf","%(years)s",3),
            ("journal_sale_vou","Sales Entry") : ("Buchung Verkauf","%(years)s",3),
            ("stock.lot.serial","Production Lots") : ("Charge/Fertigungslos",None,7),
            ("packs","Packs") : ("Gebinde",None,7),
            ("stock.orderpoint","Stock orderpoint") : ("Bestellregel","LR",None,6),
            ("stock.picking.in","Picking IN") : ("Lieferschein Eingang","EIN",None,5),
            ("stock.picking.out","Picking OUT") : ("Lieferschein Ausgang","AUS",None,5),
            ("stock.picking.int","Picking INT") : ("Lieferschein Intern","INT",None,5),       
            ("res.partner","Partner Sequence") : ("Kundennummer",None,6),                 
#            ("Account Default Bank Journal") : ("Journal Bank","BA/%(years)s",3),
#            ("Account Default Cash Journal") : ("Journal Kassa","KA/%(years)s",3),
#            ("Account Default Checks Journal") : ("Journal Kreditkarte","KR/%(years)s",3),
#            ("Account Default Expenses Credit Notes Journal") : ("Journal Lieferantengutschriften","LG/%(years)s",3),
#            ("Account Default Expenses Journal") : ("Journal Ausgaben","ER/%(years)s",3),
#            ("Account Default Miscellaneous Journal") : ("Journal Sonstiges", "SONST/%(years)s",3),
#            ("Account Default Opening Entries Journal") : ("Journal Eröffnungsbuchungen","EB/%(years)s",3),
#            ("Account Default Sales Credit Note Journal") : ("Journal Kundengutschrift", "KG/%(years)s",3),
#            ("Account Default Sales Journal") : ("Journal Ausgangsrechnungen", "AR/%(years)s",3),           
   
          
        }
        
        seq_code_map = {}
        for key, value in seq_map.items():
            if key[0]:
                seq_code_map[key[0]]=value
        
        account_type_map = {
            "asset" : "Aktiva" ,
            "cash" : "Kassa/Bank" ,
            "equity" : "Eigenkapital/Abschluss",
            "expense" : "Aufwände",
            "income" : "Erlöse",
            "liability" : "Passiva",
            "payable" : "Kreditor",
            "receivable" : "Debitor",
            "tax" : "Steuern",
            "view" : "Ansicht"
        }
        
        journal_map = {
            "ECNJ" : ("LG","Lieferantengutschrift"),
            "EXJ" : ("ER","Eingangsrechnung"),
            "MISC" : ("S","Sonstiges"),
            "SAJ" : ("AR","Ausgangsrechnung"),
            "SCNJ" : ("KG","Kundengutschrift"),
            "STJ" : ("L","Lager"),
            "OBEJ" : ("EB","Kontoeröffnung")
        }
        
                
        seq_type_obj = self.pool.get("ir.sequence.type")
        seq_obj = self.pool.get("ir.sequence")
        acc_journal_obj = self.pool.get("account.journal")
        acc_type_obj = self.pool.get("account.account.type")
        
        # pass sequence types
        for seq_type in seq_type_obj.browse(cr,uid,seq_type_obj.search(cr,uid,[])):
            value = seq_code_map.get(seq_type.code)
            name = value and value[0] or None

            if name:
                seq_type_obj.write(cr,uid,seq_type.id,{"name" : name })
            else:
                _logger.warning("Sequence type %s not in map!" % (seq_type.code,))
                
        # pass sequences
        for seq in seq_obj.browse(cr,uid,seq_obj.search(cr,uid,[])):
            key = seq.code and (seq.code,seq.name) or (seq.name)            
            res = seq_map.get(key)
            
            if not res and seq.code:
                res = seq_code_map.get(seq.code)
            
            if res:
                values = {"name" : res[0]}
                if wizard.update_seq:
                    values["prefix"]=res[1]
                    values["padding"]=res[2]                    
                seq_obj.write(cr,uid,seq.id,values)
            else:
                if wizard.delete_unassigned and not seq.code:
                    assinged_journal_ids = acc_journal_obj.search(cr,uid,[("sequence_id","=",seq.id)])
                    if not assinged_journal_ids:
                        _logger.info("Delete Sequence %s" % (seq.name,))
                        seq_obj.unlink(cr,uid,seq.id)
                _logger.info("No Sequence Update for %s" % (seq.name,))
        
        for acc_type in acc_type_obj.browse(cr,uid,acc_type_obj.search(cr,uid,[])):
            name = account_type_map.get(acc_type.code)
            if name:
                acc_type_obj.write(cr,uid,[acc_type.id],{ "name" : name })
            else:
                _logger.info("Account type %s not in map!" % (acc_type.code,))
                
        
        for acc_journal in acc_journal_obj.browse(cr,uid,acc_journal_obj.search(cr,uid,[])):
            res = journal_map.get(acc_journal.code)
            if res:
                acc_journal_obj.write(cr,uid,[acc_journal.id], {
                            "code" : res[0],
                            "name" : res[1]
                })
            else:
                _logger.info("No Journal Update for %s" % (acc_journal.code,))
                
        return super(austrian_erp_wizard,self).action_next(cr, uid, ids, context=context)


    _name = "l10n_chart_at_2010.austrian_erp_wizard"
    _description = "Austrian ERP Adaptation Wizard"
    _inherit = "res.config"
    _columns = {            
        "update_seq" : fields.boolean("Update Sequences"),
        "delete_unassigned" : fields.boolean("Delete Unassigned Sequences")
    }        
    
