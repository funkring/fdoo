# -*- coding: utf-8 -*-
#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martinr@funkring.net>
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
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
from openerp.addons.at_base import util
import openerp.addons.decimal_precision as dp

import base64


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class sale_shop(osv.osv):
    
    _name = "sale.shop"
    _description = "Shop"
    _columns = {
        "name" : fields.char("Name",size=32,required=True,select=True),
        "payment_default_id": fields.many2one("account.payment.term", "Payment Term", required=True, select=True),
        "warehouse_id": fields.many2one("stock.warehouse", "Warehouse"),
        "pricelist_id": fields.many2one("product.pricelist", "Pricelist"),
        "project_id": fields.many2one("account.analytic.account", "Analytic Account", domain=[("parent_id", "!=", False), ("type","!=","view")], ondelete="restrict"),
        "company_id": fields.many2one("res.company", "Company", required=False),
        "note" : fields.text("Note"),
        "code": fields.char("Code", size=8),
        "invoice_text" : fields.text("Sale Invoice Text"),
        "invoice_in_text" : fields.text("Purchase Invoice Text"),
        "refund_text" : fields.text("Customer Refund Text"),
        "refund_in_text" : fields.text("Supplier Refund Text"),
        "report_ids" : fields.one2many("sale.shop.report", "shop_id", "Reports"),
        "stylesheet_id": fields.many2one("report.stylesheets", "Aeroo Global Stylesheet"),
        "stylesheet_landscape_id": fields.many2one("report.stylesheets", "Aeroo Global Landscape Stylesheet"),
        "stylesheet_intern_id" : fields.many2one("report.stylesheets", "Aeroo Intern Stylesheet"),
        "stylesheet_intern_landscape_id" : fields.many2one("report.stylesheets", "Aeroo Intern Landscape Stylesheet")
    }
    _defaults = {
        "company_id": lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.shop', context=c),
    }


class sale_shop_report(osv.osv):

    _name = "sale.shop.report"
    _description = "Shop Report"
    _columns = {
        "name" : fields.char("Name", size=64),
        "shop_id" : fields.many2one("sale.shop", "Shop",on_delete="cascade",required=True),
        "source_report_id" : fields.many2one("ir.actions.report.xml", "Source Report",on_delete="cascade",required=True),
        "dest_report_id" : fields.many2one("ir.actions.report.xml", "Destination Report",on_delete="cascade",required=True),
    }


class report_xml(osv.osv):

    def _get_replacement(self, cr, uid, obj, report_xml, context=None):
        style_io = None
        repl_report = None
        
        def toBinaryContent(style):
            if style:
                content = style.report_styles
                bin_content = StringIO()
                bin_content.write(base64.decodestring(content))
                return bin_content
            return None
        
        # check shop_id and search fore replacement report
        if hasattr(obj, "shop_id"):
            shop = obj.shop_id
            if shop:                
                report_obj = self.pool.get("sale.shop.report")
                report_ids = report_obj.search(cr, uid, [("shop_id","=",shop.id),("source_report_id","=",report_xml.id)])
                if report_ids:
                    report = report_obj.browse(cr, uid, report_ids[0], context=context)
                    repl_report = report.dest_report_id
                
                # search template
                styles_mode = report_xml.styles_mode
                if styles_mode != "default":
                    # get intern                    
                    if styles_mode == "intern":
                        style_io = toBinaryContent(shop.stylesheet_intern_id)
                    elif styles_mode == "intern_landscape":
                        style_io = toBinaryContent(shop.stylesheet_intern_landscape_id)
                    # get global
                    if not style_io:
                        if styles_mode == "global" or styles_mode == "intern":
                            style_io = toBinaryContent(shop.stylesheet_id)
                        elif styles_mode == "global_landscape" or styles_mode == "intern_landscape":
                            style_io = toBinaryContent(shop.stylesheet_landscape_id)
                        
        return (repl_report, style_io)

    _inherit = "ir.actions.report.xml"


class sale_order(osv.osv):

    def _last_invoice(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):

            cr.execute("SELECT sale_order_invoice_rel.invoice_id FROM sale_order_invoice_rel "
                               "  INNER JOIN account_invoice ON account_invoice.id = sale_order_invoice_rel.invoice_id "
                               "  WHERE sale_order_invoice_rel.order_id = %s ORDER BY account_invoice.date_invoice DESC LIMIT 1 "
                                % (obj.id))

            sql_res = cr.fetchall()
            if sql_res:
                res[obj.id]=sql_res[0]
        return res

    def _tax_amount(self,cr,uid,oid,context=None):
        """
        RETURN: {
                tax.id: 0.0
            }
        """
        res = {}
        order_rec = self.browse(cr, uid, oid, context)
        for line_rec in order_rec.order_line:
            tax_calc = self.pool.get("account.tax").compute_all(cr, uid, line_rec.tax_id,
                                            line_rec.price_unit * (1-(line_rec.discount or 0.0)/100.0), line_rec.product_uom_qty,
                                            line_rec.product_id.id, line_rec.order_id.partner_id.id)
            for tax in tax_calc["taxes"]:
                tax_id = tax["id"]
                tax_amount = tax.get("amount",0.0)
                amount = res.get(tax_id,0.0)
                amount += tax_amount
                res[tax_id] = amount
        return res

    def copy(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}

        client_order_ref = default.get("client_order_ref",None)
        if not client_order_ref:
            order = self.browse(cr, uid, oid, context)
            client_order_ref = order.client_order_ref
            if client_order_ref:
                client_order_ref = client_order_ref + " " + _("Copy")
            else:
                client_order_ref = order.name + " " + _("Copy")

        default.update({
            "client_order_ref": client_order_ref
        })
        return super(sale_order, self).copy(cr, uid, oid, default=default, context=context)

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(sale_order,self).default_get(cr,uid,fields_list,context)
        payment_term = res.get("payment_term")
        shop_id = res.get("shop_id")
        if not payment_term and shop_id:
            shop = self.pool.get("sale.shop").browse(cr,uid,shop_id)
            res["payment_term"]=shop.payment_default_id and shop.payment_default_id.id or None
        return res

    def onchange_partner_id(self, cr, uid, ids, part, context=None, shop_id=None):
        res = super(sale_order,self).onchange_partner_id(cr,uid,ids,part,context=context)
        value = res.get("value")
        if value:
            payment_term = value.get("payment_term")
            if not payment_term and shop_id:
                shop = self.pool.get("sale.shop").browse(cr,uid,shop_id)
                value["payment_term"]=shop.payment_default_id and shop.payment_default_id.id or None
        return res

    def onchange_shop_id(self, cr, uid, ids, shop_id, state, context=None):
        value = {}
        res = { "value": value }
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
            if shop.note:
                value["note"] = shop.note
            if shop.company_id and state == "draft":
                value["company_id"] = shop.company_id
        return res

    def action_wait(self, cr, uid, ids, context=None):
        #convert from non customer to customer
        partner_obj = self.pool.get("res.partner")
        should_customers_ids = partner_obj.search(cr,uid,[("id","in",ids),("customer","=",False)])
        partner_obj.write(cr, uid, should_customers_ids, {
                "customer" : True
            },context=context)
        return super(sale_order,self).action_wait(cr,uid,ids,context=context)

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        res = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        res["shop_id"] = order.shop_id.id
        return res 
  
    def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
        start_date = util.strToTime(start_date)
        company = order.company_id
        date_planned = None

        real_delay = (line.delay or 0.0) - company.security_lead
        if real_delay:
            if company.calendar_id:
                date_planned = self.pool.get('resource.calendar').passed_range(cr,uid,company.calendar_id.id,start_date,real_delay)["to"]
            else:
                date_planned = start_date + relativedelta(days=real_delay)
        if date_planned:
            date_planned = util.timeToStr(date_planned)
        else:
            return util.currentDate()
        return date_planned

    def _default_shop_id(self, cr, uid, context=None):
        company_id = self.pool.get("res.company")._company_default_get(cr, uid, 'sale.order', context=context)
        res = None
        if company_id:
            shop_obj = self.pool.get("sale.shop")
            res = shop_obj.search_id(cr, uid, [("company_id","=",company_id)],context=context)
            if not res:
                res = shop_obj.search_id(cr, uid, [("company_id","=",False)],context=context)
        return res

    _inherit = "sale.order"
    _columns = {
        "shop_id" : fields.many2one("sale.shop", "Shop", type="many2one", required=True, readonly=True, states={'draft': [('readonly', False)]}),
        "last_invoice_id" : fields.function(_last_invoice, string="Last Invoice", readonly=True, type='many2one', relation="account.invoice")
    }
    _defaults = {
        "shop_id" : _default_shop_id,
    }


class sale_order_line(osv.osv):

    def _amount_line_taxed(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = dict.fromkeys(ids)
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty,
                                         line.product_id.id, line.order_id.partner_id.id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
        return res
    
    def _price_unit_untaxed(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = dict.fromkeys(ids)
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty,
                                         line.product_id.id, line.order_id.partner_id.id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'] / line.product_uom_qty)
        return res

    def _line_sum(self, cr, uid, ids, context=None):
        """
        RETURN: {
                'total': 0.0,                # Total without taxes
                'total_included: 0.0,        # Total with taxes
                'amount_taxes' : 0.0,        # Taxes Amount
                'taxes': [{
                     {'name':'', 'amount':0.0, 'account_collected_id':1, 'account_paid_id':2}
                }]  # List of taxes, see compute for the format
            }
        """
        res = {}
        total = 0.0
        amount_taxes = 0.0
        taxes = []

        for line in self.browse(cr, uid, ids):
            total += line.price_subtotal
            tax_id = line.tax_id
            for tax in (self.pool.get('account.tax').compute_all(cr, uid, tax_id,
                                                               line.price_unit * (1-(line.discount or 0.0)/100.0),
                                                               line.product_uom_qty,
                                                               line.product_id.id, line.order_id.partner_id.id)['taxes']):
                amount_taxes += tax.get('amount', 0.0)
                taxes.append(tax)

        res["total_included"] = total + amount_taxes
        res["total"] = total
        res["amount_taxes"] = amount_taxes
        res["taxes"] = taxes
        return res

    _inherit = "sale.order.line"
    _columns = {
        "price_subtotal_taxed" : fields.function(_amount_line_taxed,string="Subtotal (Brutto)",digits_compute= dp.get_precision("Sale Price")),
        "price_unit_untaxed" : fields.function(_price_unit_untaxed,string="Price Untaxed",digits_compute= dp.get_precision("Sale Price"))
    }

