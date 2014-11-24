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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.addons.at_base import util
from openerp.addons.at_base import format
from openerp.tools.translate import _

class academy_invoice_assistant(osv.osv_memory):
    
    def onchange_semester(self, cr, uid, ids, semester_id, context=None):
        values = {}
        res = { "value" : values }
        
        if semester_id:
            values["customer_ref"] = self.pool["academy.semester"].name_get(cr, uid, [semester_id], context=context)[0][1]
            
        return res
        
    def action_invoice(self, cr, uid, ids, context=None):
        invoice_obj = self.pool["account.invoice"]
        invoice_line_obj = self.pool["account.invoice.line"]
        reg_obj = self.pool["academy.registration"]
        reg_inv_obj = self.pool["academy.registration.invoice"]
        fee_obj = self.pool["academy.fee"]

        wizard = self.browse(cr, uid, ids[0], context=context)
        semester = wizard.semester_id
        
        # registration query filter
        reg_query = []
        sel_reg_ids = util.active_ids(context,"academy.registration")
        if sel_reg_ids:
            reg_query.append(("id","in",sel_reg_ids))
            
        # state filter
        reg_query.append("!")
        reg_query.append(("state","in",["draft","cancel","check"]))
        
        # search valid registration ids
        reg_ids = reg_obj.search(cr, uid, reg_query)

        # get semester weeks        
        sem_weeks = semester.semester_weeks
        f = format.LangFormat(cr, uid, context=context)
        # group registrations
        invoices = {}        
        for reg in reg_obj.browse(cr, uid, reg_ids, context=context):
            # check if invoice for registration exist
            reg_inv_id = reg_inv_obj.search_id(cr, uid, [("registration_id","=",reg.id),("semester_id","=",semester.id)], context=context)
            if reg_inv_id:
                continue
        
            # get invoice address
            student = reg.student_id        
            partner = reg.use_invoice_address_id
            
            # invoice context
            inv_context = context and dict(context) or {}
            inv_context["type"] = "out_invoice"
                
            # get invoice or create new
            invoice_id = invoice_obj.search_id(cr, uid, [("state","=","draft"),("partner_id","=",partner.id)])
            if not invoice_id:
                # invoice values            
                inv_values = {
                    "partner_id" : partner.id,
                    "name" : wizard.customer_ref
                }            
                            
                inv_values.update(invoice_obj.onchange_partner_id(cr, uid, [], "out_invoice", partner.id, context=context)["value"])
                invoice_id = invoice_obj.create(cr, uid, inv_values, context=context)
                
            # get new invoice
            invoice = invoice_obj.browse(cr, uid, invoice_id, context=context)
            # get fees
            fees = fee_obj.browse(cr, uid, fee_obj.search(cr, uid, []), context=context)
            
            
            # create line
                        
            # add product function
            def addProduct(product, uos_id=None, discount=0.0, discount_reason=None):
                line = { "invoice_id" : invoice_id,
                         "product_id" : product.id,
                         "quantity" : 1.0,
                         "uos_id" : uos_id or product.uos_id.id
                        }
                
                if discount:
                    line["discount"]=discount
                                    
                line.update(invoice_line_obj.product_id_change(cr, uid, [],
                                line["product_id"], line["uos_id"], qty=line["quantity"],
                                type=invoice.type, 
                                partner_id=invoice.partner_id.id, 
                                fposition_id=invoice.fiscal_position.id, 
                                company_id=invoice.company_id.id, 
                                currency_id=invoice.currency_id.id,
                                context=inv_context)["value"])
                
                tax_ids = line.get("invoice_line_tax_id")
                if tax_ids:
                    line["invoice_line_tax_id"]=[(6,0,tax_ids)]
                
                # discount reason
                if discount_reason:
                    line["name"] = _("%s - %s\n%s\n%s") % (reg.name, line["name"], 
                                                           reg.student_id.name, 
                                                           discount_reason)
                # or default
                else:
                    line["name"] = _("%s - %s\n%s") % (reg.name, line["name"], 
                                                       reg.student_id.name)
                    
                return invoice_line_obj.create(cr, uid, line, context=context)
            
            
            # create line
            
            # calc discount
            discount = 0.0
            discount_reason = None            
            if reg.intership_date:
                intership_dt = util.strToDate(reg.intership_date)
                if intership_dt > sem_start_dt and intership_dt < sem_end_dt:
                    missed_duration = intership_dt - sem_start_dt
                    missed_weeks = int(round(missed_duration.days/7.0))
                    if missed_duration:
                        discount = (100.0/sem_weeks) * missed_weeks
                        discount_reason = _("Intership discount for %s missed weeks") % missed_weeks
                                      
     
            addProduct(reg.course_prod_id.product_id, reg.uom_id.id, discount=discount, discount_reason=discount_reason)
            
                          
            # add fees
            
            location = reg.location_id
            category_set = set([c.id for c in reg.location_id.category_id])
            
            for fee in fees:
                # check if uom is used and match
                if fee.apply_uom_id and fee.uom_id.id != reg.uom_id.id:
                    continue
                
                # check if categories match
                if fee.location_category_ids:
                    has_category = False
                    for category in fee.location_category_ids:
                        if category.id in category_set:
                            has_category = True
                            break
                    if not has_category:
                        continue
                                                            
                # check for discount
                discount = 0.0
                if fee.sibling_discount:
                    parent = student.partner_id.parent_id
                        
                    fee_query = (" SELECT COUNT(l.id) FROM account_invoice_line l "
                                " INNER JOIN account_invoice inv ON inv.id = l.invoice_id "
                                " INNER JOIN academy_registration_invoice rinv ON rinv.invoice_id = inv.id AND rinv.semester_id = %s "
                                " INNER JOIN academy_registration r ON r.id = rinv.registration_id "
                                " INNER JOIN academy_student s ON s.id = r.student_id "
                                " INNER JOIN res_partner p ON p.id = s.partner_id "
                                " WHERE l.product_id = %s "
                                "   AND l.quantity > 0 AND l.discount < 100 "
                                "   AND %s " % (semester.id, fee.product_id.id, 
                                                parent and ("(p.parent_id = %s OR p.id = %s) " % (parent.id,student.partner_id.id )) or ("p.id = %s " % student.partner_id.id) ))
                    cr.execute(fee_query)
                    rows = cr.fetchone()       
                    # already invoiced ?
                    if rows and rows[0]:
                        discount = fee.sibling_discount
                       
                # add fee
                addProduct(fee.product_id, discount=discount)
              
                
            # create invoice link
            reg_inv_obj.create(cr, uid, { "registration_id" : reg.id,
                                          "semester_id" : semester.id,
                                          "invoice_id" : invoice_id})      
            
            # write origin
            origin = reg.name
            if invoice.origin and origin:
                origin = "%s:%s" % (invoice.origin,origin)
            invoice_obj.write(cr, uid, invoice_id, { "origin" : origin}, context=context)
            
            # validate invoice
            invoice_obj.button_compute(cr, uid, [invoice_id], context=context)
        
        return { "type" : "ir.actions.act_window_close" }
    
    def _default_semester_id(self, cr, uid, fields, context=None):
        user = self.pool["res.users"].browse(cr, uid, uid, context=context)
        return user.company_id.academy_semester_id.id

    _name = "academy.invoice.assistant"
    _rec_name = "semester_id"
    _columns = {
        "semester_id" : fields.many2one("academy.semester", "Semester", required=True),
        "customer_ref" : fields.char("Reference")
    }
    _defaults = {
        "semester_id" : _default_semester_id
    }
