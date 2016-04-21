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

from openerp.report import report_sxw
from openerp.tools.translate import _
from collections import OrderedDict
from openerp.addons.at_base import util

from wand.image import Image
from wand.color import Color
import os
import base64

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):        
        super(Parser, self).__init__(cr, uid, name, context=context)
        print_detail = name == "account.bank.statement.detail"
        if context:
            print_detail = context.get("print_detail", print_detail)  
        self.localcontext.update({
            "get_detail" : self._get_detail,
            "print_detail" : print_detail      
        })
        
           
    def _get_detail(self, statement):
        line_vals = []
        invoice_obj = self.pool.get("account.invoice")
        report_obj = self.pool.get("ir.actions.report.xml")
        att_obj = self.pool.get("ir.attachment")
        invoice_set = set()
        images = []
        print_detail = self.localcontext.get("print_detail")
        
        inv_report = None
        inv_report_context = None
        
        # ADD ATTACHMENT FUNCTION
        def addAttachments(obj, pos):
            # add attachments
            att_ids = att_obj.search(self.cr, self.uid, [("res_model","=",obj._model._name),("res_id","=",obj.id)])
            for att in att_obj.browse(self.cr, self.uid, att_ids, context=self.localcontext):
                fname = att.datas_fname
                if not fname:
                    continue
                if not fname.lower().endswith(".pdf"):
                    continue
                
                datas = att.datas
                if not datas:
                    continue
                
                datab = base64.decodestring(datas)
                if not datab:
                    continue
                
                im = Image(blob=datab, resolution=150)
                bk = Color("white")
                for i, page in enumerate(im.sequence):
                    with Image(page) as page_image:
                        page_image.format = "png"
                        page_image.background_color = bk
                        page_image.alpha_channel = False
                        if page_image.width > page_image.height:
                            page_image.rotate(90)
                            
                        buf = StringIO()
                        page_image.save(buf)
                        
                        if buf:
                            image_datas = base64.encodestring(buf.getvalue())
                            images.append({"pos" : pos, 
                                           "image" : image_datas})

        # add details
        if print_detail:
            addAttachments(statement,0)
            
        # get lines
        pos = 1
        for line in statement.line_ids:
            invoices = []            
            move = line.journal_entry_id
            if move:
                move_ids = [x.id for x in move.line_id]
                if move_ids:
                    self.cr.execute("SELECT inv.id FROM account_invoice inv "
                        " INNER JOIN account_move_line m ON m.move_id = inv.move_id AND m.account_id = inv.account_id "
                        " INNER JOIN account_move_reconcile r ON r.id = m.reconcile_id OR r.id = m.reconcile_partial_id "
                        " INNER JOIN account_move_line m2 ON m2.reconcile_id = r.id OR m2.reconcile_partial_id = r.id "
                        " WHERE m2.id in %s GROUP BY 1 ", (tuple(move_ids),))
                     
                    invoice_ids = [r[0] for r in self.cr.fetchall()]
                    if invoice_ids:
                        invoices = invoice_obj.browse(self.cr, self.uid, invoice_ids, context=self.localcontext)
               
            line_vals.append({
                "line" : line,
                "invoices" : invoices,
                "pos" : pos
            })
            
            # add details
            if print_detail:
                for inv in invoices:
                    if not inv.id in invoice_set:
                        invoice_set.add(inv.id)
                        
                        # update report,
                        # if it is an self produced invoice
                        if inv.type in ("out_invoice","out_refund"):
                            if not inv_report:
                                inv_report = report_obj._lookup_report(self.cr, "account.report_invoice")
                                report_context = dict(self.localcontext)
                                report_context["report_title"] = _("Invoice")
                            if inv_report:
                                inv_report.create(self.cr, self.uid, [inv.id], {"model":"account.invoice"}, report_context)
                            
                        # add attaments
                        addAttachments(inv, pos)
                        
            pos += 1
            
        return [{
            "lines" : line_vals,
            "images" : images
        }]
    
 