# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.addons.at_base import helper
from openerp.addons.at_base.format import LangFormat
from openerp.addons.at_base import util

class commission_invoice_wizard(osv.osv_memory):
    
    def _name_default(self,cr,uid,context=None):
        date_min = None
        date_max = None
        commission_line_obj = self.pool.get("commission.line")
        
        for line in commission_line_obj.browse(cr, uid, 
                                               util.active_ids(context, commission_line_obj), 
                                               context=context):
            if not date_min or line.period_id.date_start < date_min:
                date_min = line.period_id.date_start
            if not date_max or line.period_id.date_stop > date_max:
                date_max = line.period_id.date_stop
        return _("Provision %s") % (helper.getRangeName(cr, uid, date_min, date_max,context),)
      
    def _inv_line_name_get(self,cr,uid,wizard,analytic_line,context=None):
        f = LangFormat(cr, uid, context=context)
        infos = []
        
        def addInfo(val):
          if not val:
            return
          val = val.strip()
          if not val:
            return
          for info in infos:
            if val in info:
              return
          infos.append(val)
        
        if analytic_line:
            # add date
            if analytic_line.date:
              addInfo(f.formatLang(analytic_line.date,date=True))
            # add standard line info
            addInfo(analytic_line.ref)
            addInfo(analytic_line.name)
            # add detailed invoice info
            if wizard.detail_ref:
              invoice = analytic_line.invoice_id
              if invoice:
                addInfo(invoice.number)
                addInfo(invoice.name)
                
        return " / ".join(infos) or ""
      
    def _inv_line_note_get(self,cr,uid,wizard,analytic_line,context=None):
        f = LangFormat(cr, uid, context=context)
        cur = analytic_line.currency_id.symbol or analytic_line.currency_id.name or ""
        
        if analytic_line.base_commission == analytic_line.total_commission:
            if analytic_line.val_based:
                return None 
            return _("%s %% Commission from %s %s") % (f.formatLang(analytic_line.base_commission),f.formatLang(analytic_line.price_sub, dp="Sale Price"),cur)
        
        if analytic_line.base_commission < analytic_line.total_commission:
            return _("%s %% Commission +%s %% Bonus from %s %s") % (f.formatLang(analytic_line.base_commission),
                                                                                analytic_line.total_commission-analytic_line.base_commission, 
                                                                                f.formatLang(analytic_line.price_sub, dp="Sale Price"),cur)
        else:
            return _("%s %% Commission -%s %% Malus from %s %s") % (f.formatLang(analytic_line.base_commission),
                                                                                analytic_line.base_commission-analytic_line.total_commission, 
                                                                                f.formatLang(analytic_line.price_sub, dp="Sale Price"),cur)
            
    def do_create(self,cr,uid,ids,context=None):
        invoice_line_obj = self.pool.get("account.invoice.line")
        invoice_obj = self.pool.get("account.invoice")
        fiscal_pos_obj = self.pool.get("account.fiscal.position")
        partner_obj = self.pool.get("res.partner")
        commission_line_obj = self.pool.get("commission.line")
        journal_obj = self.pool.get("account.journal")
        shop_obj = self.pool.get("sale.shop")
        wizard = self.browse(cr, uid, ids[0], context)        

        partner = None
        invoice_ids = []
        detail = wizard.detail_ref
        lineMap = {}
        
        if context is None:
            context = {}
       
        line_ids = commission_line_obj.search(cr,uid,[("id","in",util.active_ids(context))],order="partner_id, date asc")
        for line in commission_line_obj.browse(cr, uid, line_ids):
            # group partners
            if not partner or partner.id != line.partner_id.id:
                # reset
                sequence = 100
              
                # get objects
                partner = line.partner_id
                salesman = line.salesman_id                
                team = salesman and salesman.default_section_id or None
                company = line.company_id

                # prepare context
                inv_type = "in_invoice"
                if company.commission_refund:
                  inv_type = "out_refund"
                
                invContext = dict(context)
                invContext["type"] = inv_type
                
                # get values                
                inv_values = {
                  "type" : inv_type,
                  "name" : wizard.name,
                  "reference" : wizard.name,
                  "origin" : wizard.name,
                  "partner_id" : partner.id,
                  "company_id" : company.id,
                  "currency_id": company.currency_id.id
                }
                
                if team:
                    shop_id = shop_obj.search_id(cr, uid, [("team_id","=",team.id)], context=invContext)
                    if shop_id:
                        inv_values["shop_id"] = shop_id
                
                helper.onChangeValuesPool(cr, uid, invoice_obj, inv_values, 
                                invoice_obj.onchange_company_id(cr, uid, [], company.id, partner.id, inv_type, None, inv_values["currency_id"], context=invContext), context=context)
                                
                helper.onChangeValuesPool(cr, uid, invoice_obj, inv_values, 
                                invoice_obj.onchange_partner_id(cr, uid, [], inv_type, partner.id, company_id=company.id, context=invContext), context=context)
                
                helper.onChangeValuesPool(cr, uid, invoice_obj, inv_values,
                                invoice_obj.onchange_journal_id(cr, uid, [], inv_values["journal_id"], context=invContext), context=context)

                # check for fiscal position override
                if company.commission_novat_fp and not partner.vat:
                  inv_values["fiscal_position"] = company.commission_novat_fp.id
                  
                # check for commission text
                if company.commission_text:
                  inv_values["comment"] = company.commission_text
                                
                invoice_id = invoice_obj.create(cr, uid, inv_values, context=invContext)
                invoice_ids.append(invoice_id)

            product = line.product_id
            price_unit = line.amount*-1
            sequence += 1
            
            values = {
                "invoice_id" : invoice_id,
                "price_unit" : price_unit,
                "quantity" : 1.0,
                "name" : line.name,                
                "product_id" : product.id,               
                "uos_id" : line.product_uom_id.id,
                "account_id" : line.general_account_id.id,
                "account_analytic_id" : line.account_id.id,
                "origin" : line.ref,
                "sequence": sequence
            }
            
            helper.onChangeValuesPool(cr, uid, invoice_line_obj, values, 
                     invoice_line_obj.product_id_change(cr, uid, [],
                                               values["product_id"],
                                               values["uos_id"],
                                               values["quantity"],
                                               values["name"],
                                               type=inv_values["type"],
                                               partner_id=inv_values["partner_id"],
                                               fposition_id=inv_values.get("fiscal_position"),
                                               price_unit=price_unit,
                                               currency_id=inv_values["currency_id"],
                                               company_id=company.id,
                                               context=invContext), context=context)

            values["price_unit"] = price_unit
            values["name"] = self._inv_line_name_get(cr, uid, wizard, line, invContext)            
            values["note"] = self._inv_line_note_get(cr, uid, wizard, line, invContext)
                    
            if detail and line.sale_partner_id:
                
                sale_partner = line.sale_partner_id 
                salePartnerDetail = lineMap.get(sale_partner.id)
                
                if salePartnerDetail is None:
                    salePartnerDetail = {
                        "name" : sale_partner.name_get()[0][1],
                        "invoice_id" : invoice_id,
                        "context" : invContext,
                        "sequence" : values["sequence"],
                        "lines" : []
                    }
                    
                    # update sequence
                    sequence += 1
                    values["sequence"] = sequence
                    
                    lineMap[sale_partner.id] = salePartnerDetail
                
                salePartnerDetail["lines"].append((line,values))
                
            else:
                invoice_line_id = invoice_line_obj.create(cr, uid, values, context=invContext)
                commission_line_obj.write(cr,uid,line.id,{"invoiced_id" : invoice_id,
                                                          "invoiced_line_ids" : [(4,invoice_line_id)]
                                                        })
               
        # write detail
        if lineMap:
            # sort partners by name
            salePartners = sorted(lineMap.values(), key=lambda v: v["name"])
            for salePartner in salePartners:
                # create header           
                invContext = salePartner["context"]     
                invoice_line_obj.create(cr, uid, {
                    "invoice_id" : salePartner["invoice_id"],
                    "price_unit" : 0.0,
                    "quantity" : 0.0,
                    "invoice_line_tax_id" : [(6,0,[])],
                    "name" : salePartner["name"],
                    "sequence": salePartner["sequence"]                    
                }, context=invContext)
                
                # create lines
                for line, values in salePartner["lines"]:
                    invoice_line_id = invoice_line_obj.create(cr, uid, values, context=invContext)
                    commission_line_obj.write(cr, uid, line.id, {
                        "invoiced_id" : salePartner["invoice_id"],
                        "invoiced_line_ids" : [(4,invoice_line_id)]
                    })
                    
        # update invoices                       
        if invoice_ids:
            invoice_obj.button_compute(cr, uid, invoice_ids, set_total=True, context=context)
            
            # Show Invoices
            mod_obj = self.pool.get("ir.model.data")
            act_obj = self.pool.get("ir.actions.act_window")

            view_id = "action_invoice_tree2"
            if inv_type == "out_refund":
              view_id = "action_invoice_tree3"
              
            mod_ids = mod_obj.search(cr, uid, [("name", "=", view_id)], context=context)[0]
            res_id = mod_obj.read(cr, uid, mod_ids, ["res_id"], context=context)["res_id"]
            act_win = act_obj.read(cr, uid, res_id, [], context=context)
            act_win["domain"] = [("id","in",invoice_ids),("type","=",inv_type)]            
            return act_win
        
        #or nothing
        return { "type" : "ir.actions.act_window_close" }
    
    _name = "commission.commission_invoice_wizard"
    _description = "Create invoice from commission"

    _columns = {
        "name" : fields.char("Description"),        
        "detail_ref" : fields.boolean("Detailed Ref.", help="Detailed Reference is displayed")
    }
    _defaults = {
        "name" : _name_default,
        "detail_ref": True
    }

