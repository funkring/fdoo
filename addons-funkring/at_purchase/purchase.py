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

from openerp.osv import osv,fields
import openerp.addons.decimal_precision as dp
from openerp.addons.at_base import util
from openerp.addons.at_base.util import SEVERITY
from openerp.addons.at_base.util import PRIORITY
from openerp.tools.translate import _

class purchase_order_level(osv.osv):
    _name = "purchase.order_level"
    _description = "Purchase Order Level"
    _columns = {
        "name" : fields.char("Name",size=32,required=True),
        "sequence" : fields.integer("Sequence"),  
        "severity": fields.selection(SEVERITY, "Severity", required=True),      
        "description" : fields.text("Description")                
    }
    _defaults = {
        "sequence" : 10
    }
    _order = "sequence, id"


class procurement_order(osv.osv):
       
    def _get_supplier_info(self,procurement):
        res = {}
        if procurement.preferred_seller_id:
            seller = procurement.preferred_seller_id
            res["partner"] = seller.name
            res["delay"] = seller.delay or 1
            res["qty"] = seller.qty or 0.0
        else:
            res["partner"] = procurement.product_id.seller_id
            res["qty"] = procurement.product_id.seller_qty 
            res["delay"] = int(procurement.product_id.seller_delay)         
        return res
   
    def _create_po(self, cr, uid, order, line, context=None):
        res = self.pool.get('purchase.order').create(cr, uid, order, context=context)
        return res
    
    def _validate_po(self, cr, uid, procurement, order, line, context=None):
        return True
    
    def make_po(self, cr, uid, ids, context=None):
        """ Make purchase order from procurement
        @return: New created Purchase Orders procurement wise
        """
        res = {}
        if context is None:
            context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        partner_obj = self.pool.get('res.partner')
        uom_obj = self.pool.get('product.uom')
        pricelist_obj = self.pool.get('product.pricelist')
        prod_obj = self.pool.get('product.product')
        acc_pos_obj = self.pool.get('account.fiscal.position')
        seq_obj = self.pool.get('ir.sequence')
        warehouse_obj = self.pool.get('stock.warehouse')
        for procurement in self.browse(cr, uid, ids, context=context):
            res_id = procurement.move_id.id
            partner = procurement.product_id.seller_id # Taken Main Supplier of Product of Procurement.
            seller_qty = procurement.product_id.seller_qty
            partner_id = partner.id
            delivery_partner_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            pricelist_id = partner.property_product_pricelist_purchase.id
            warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
            uom_id = procurement.product_id.uom_po_id.id
        
            qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
            if seller_qty:
                qty = max(qty,seller_qty)
        
            price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner_id, {'uom': uom_id})[pricelist_id]
        
            schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)
            purchase_date = self._get_purchase_order_date(cr, uid, procurement, company, schedule_date, context=context)
        
            #Passing partner_id to context for purchase order line integrity of Line name
            new_context = context.copy()
            new_context.update({'lang': partner.lang, 'partner_id': partner_id})
        
            product = prod_obj.browse(cr, uid, procurement.product_id.id, context=new_context)
            taxes_ids = procurement.product_id.supplier_taxes_id
            taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
            
            # build description
            description = []
            if product.description_purchase:
                description.append(product.description_purchase)
            if procurement.note:
                description.append(procurement.note)                                             
            description = "\n\n".join(description)        
            
            name = product.partner_ref
            if product.description_purchase:
                name += '\n'+ description
                
            line_vals = {
                'name': name,
                'product_qty': qty,
                'product_id': procurement.product_id.id,
                'product_uom': uom_id,
                'price_unit': price or 0.0,
                'date_planned': util.timeToDateStr(schedule_date), 
                'move_dest_id': res_id,
                'taxes_id': [(6,0,taxes)],
                'priority' : procurement.priority,
                'account_analytic_id' : procurement.account_analytic_id and procurement.account_analytic_id.id or None
            }
            name = seq_obj.get(cr, uid, 'purchase.order') or _('PO: %s') % procurement.name
            po_vals = {
                'name': name,
                'origin': procurement.origin,
                'partner_id': delivery_partner_id,
                'location_id': procurement.location_id.id,
                'warehouse_id': warehouse_id and warehouse_id[0] or False,
                'pricelist_id': pricelist_id,
                'date_order': util.timeToDateStr(purchase_date),
                'company_id': procurement.company_id.id,
                'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                'payment_term_id': partner.property_supplier_payment_term.id or False,
            }
            res[procurement.id] = self.create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context=new_context)
            self.write(cr, uid, [procurement.id], {'state': 'running', 'purchase_id': res[procurement.id]})
        self.message_post(cr, uid, ids, body=_("Draft Purchase Order created"), context=context)
        return res

    _inherit = 'procurement.order'
    _columns = {
        "preferred_seller_id" : fields.many2one("product.supplierinfo","Preferred Seller"),
    }   


class purchase_order_line(osv.osv):
    
    def _category_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)    
        cr.execute(
          " SELECT o.id,c.id FROM purchase_order_line AS o "
          "  INNER JOIN product_product AS p ON p.id = o.product_id "
          "  INNER JOIN product_template AS t ON p.product_tmpl_id = t.id "
          "  INNER JOIN product_category AS c ON c.id = t.categ_id "
          "  WHERE o.id IN %s",(tuple(ids),)),
        
        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res
    
    def _relids_product_template(self,cr,uid,ids,context=None):
        cr.execute(
          " SELECT o.id FROM purchase_order_line AS o "
          "  INNER JOIN product_product AS p ON p.id = o.product_id "
          "  INNER JOIN product_template AS t ON p.product_tmpl_id = t.id "
          "  INNER JOIN product_category AS c ON c.id = t.categ_id "
          "  WHERE t.id IN %s GROUP BY 1",(tuple(ids),))
        res = []
        for row in cr.fetchall():
            res.append(row[0])
        return res
    
    def _relids_purchase_order(self,cr,uid,ids,context=None):
        cr.execute(
         " SELECT l.id FROM purchase_order_line AS l " 
         "   INNER JOIN purchase_order AS o ON o.id = l.order_id "
         "   WHERE o.id IN %s GROUP BY 1", (tuple(ids),) )
        res = []
        for row in cr.fetchall():
            res.append(row[0])
        return res
    
    def _get_origin(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)            
        cr.execute(
         " SELECT l.id, o.name, o.origin FROM purchase_order_line AS l " 
         "   INNER JOIN purchase_order AS o ON o.id = l.order_id "
         "   WHERE l.id IN %s ", (tuple(ids),) )
        for row in cr.fetchall():
            order_name = row[1]
            order_origin = row[2]            
            res[row[0]]= (order_name and order_origin and "%s:%s" % (order_name,order_origin)) or order_name or order_origin or ""          
        return res
    
    def _get_directory(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute(
         " SELECT l.id, o.name  FROM purchase_order_line AS l " 
         "   INNER JOIN purchase_order AS o ON o.id = l.order_id "
         "   WHERE l.id IN %s ", (tuple(ids),) )
        
        for row in cr.fetchall():
            order_name = row[1]                        
            res[row[0]]= order_name and ("%s_%s" % (order_name,str(row[0]))) or str(row[0])
        return res
    
    def mail_quote_request(self, cr, uid, ids, context=None):        
        return True
    
    def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        res = super(purchase_order_line,self).onchange_product_uom(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, context=context)
        value = res.get("value")
        if value and product_id:
            util.removeIfEmpty(value, "price_unit")
        return res
                  
    def inv_line_create(self, cr, uid, a, ol):
        res = super(purchase_order_line,self).inv_line_create(cr,uid,a,ol)
        res[2]["purchase_lines"]=[(6,0,[ol.id])]  
        
    def _dest_picking_id(self, cr, uid, ids, field_name, arg, context):
        res = dict.fromkeys(ids)
        cr.execute("SELECT pl.id,pi.id FROM purchase_order_line pl"
           " INNER JOIN stock_move m ON m.id = pl.move_dest_id "
           " INNER JOIN stock_picking pi ON pi.id = m.picking_id "
           " WHERE pl.move_dest_id IS NOT NULL "
           " AND pl.id IN %s ", (tuple(ids),))
        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res
    
    def _src_picking_ids(self, cr, uid, ids, field_name, arg, context):
        res = dict.fromkeys(ids)
        cr.execute("SELECT pl.id,pi.id FROM purchase_order_line pl"
           " INNER JOIN stock_move m ON m.purchase_line_id = pl.id "
           " INNER JOIN stock_picking pi ON pi.id = m.picking_id "
           " WHERE pl.id IN %s ", (tuple(ids),))
        for row in cr.fetchall():
            res[row[0]]=row[1]
        return res
              
        
    _inherit = "purchase.order.line"
    _columns = {        
        "category_id" : fields.function(_category_id,type="many2one",relation="product.category",string="Category",readonly=True,select=True,
                                        store={
                                            "product.template" : (_relids_product_template,["categ_id"],10),
                                            "purchase.order.line" : (lambda self, cr, uid, ids, context=None: ids, ["product_id"],10)
                                        }),
        "directory" : fields.function(_get_directory,type="char",size=64,string="Directory"),
        "priority": fields.selection(PRIORITY, "Priority"),
        "level_id" : fields.many2one("purchase.order_level","Level"),        
        "severity": fields.related("level_id","severity",type="selection",selection=SEVERITY, string="Severity",readonly=True,store=True),
        "supplier_invoiced" : fields.boolean("Invoiced",help="Has Supplier invoiced?"),
        "supplier_unit_price" : fields.float("Supplier Unit Price",digits_compute=dp.get_precision("Purchase Price")),
        "origin": fields.function(_get_origin,type="char",string="Origin",readonly=True,select=True,
                                  store={ 
                                    "purchase.order" : (_relids_purchase_order,["origin","name"],10),
                                    "purchase.order.line" : (lambda self, cr, uid, ids, context=None: ids, ["order_id"],10)
                                   }), 
        "dest_picking_id" : fields.function(_dest_picking_id, type="many2one", obj="stock.picking", string="Destination Picking"),
        "source_picking_ids" : fields.function(_src_picking_ids,type="many2many", obj="stock.picking", string="Source Pickings"),                                                                                                                             
        "write_date" :  fields.datetime("Write Date"),
        "create_date" : fields.datetime("Creation Date")
    }
    _order = "date_planned desc, write_date desc"
