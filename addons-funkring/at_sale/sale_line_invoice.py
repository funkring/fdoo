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

from openerp.osv import osv,fields
from openerp.tools.translate import _
from openerp import workflow

class sale_order_line_make_invoice(osv.osv_memory):
        
    def make_invoices(self, cr, uid, ids, context=None):
        """
             To make invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        
        res = False
        group = self.browse(cr, uid, ids[0], context).group
        invoices = {}
        partner_invoices = {}   
             
        def concat(first,second):
            if first and second:
                return "%s:%s" % (first,second)
            elif first:
                return first
            elif second:
                return second
            return ""                
             
    #TODO: merge with sale.py/make_invoice
        def make_invoice(order, lines):
            """
                 To make invoices.

                 @param order:
                 @param lines:

                 @return:

            """
            a = order.partner_id.property_account_receivable.id            
            payterm_id = order.payment_term and order.payment_term.id or None
            partner_id = order.partner_id.id
           
            invoice_name = order.client_order_ref or order.name
            invoice_origin = order.name
            invoice_reference = order.client_order_ref or order.name
            
            if group:
                last_invoice = partner_invoices.get(partner_id)
                if last_invoice:
                    inv_add =  {
                        "name" : concat(last_invoice["name"],invoice_name),
                        "origin" : concat(last_invoice["origin"],invoice_origin),
                        "reference" : concat(last_invoice["reference"],invoice_reference),
                        "invoice_line" : ([(4,x) for x in lines])
                    }                    
                    self.pool.get('account.invoice').write(cr, uid, last_invoice["id"],inv_add,context)
                    return last_invoice["id"]    
            
            inv = {
                'name': invoice_name,
                'origin': invoice_origin,
                'type': 'out_invoice',
                'reference': invoice_reference,
                'account_id': a,
                'partner_id': order.partner_id.id,
                'address_invoice_id': order.partner_invoice_id.id,
                'address_contact_id': order.partner_invoice_id.id,
                'invoice_line': [(6, 0, lines)],
                'currency_id' : order.pricelist_id.currency_id.id,
                'comment': order.note,
                'payment_term': payterm_id,
                'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            }
            inv_id = self.pool.get('account.invoice').create(cr, uid, inv, context)
            if group:
                partner_invoices[partner_id]={ "id" : inv_id, 
                                               "name" : invoice_name, 
                                               "origin" : invoice_origin,
                                               "reference" : invoice_reference }
            return inv_id

        sale_line_ids =context.get('active_ids', [])
        stock_picking_obj = self.pool.get("stock.picking")
        sales_order_line_obj = self.pool.get('sale.order.line')
        sales_order_obj = self.pool.get('sale.order')
        for line in sales_order_line_obj.browse(cr, uid, sale_line_ids, context=context):
            if (not line.invoiced) and (line.state not in ('draft', 'cancel')):
                if not line.order_id.id in invoices:
                    invoices[line.order_id.id] = []
                line_id = sales_order_line_obj.invoice_line_create(cr, uid, [line.id])
                for lid in line_id:
                    invoices[line.order_id.id].append((line, lid))
                sales_order_line_obj.write(cr, uid, [line.id],
                        {'invoiced': True})
        for result in invoices.values():
            order = result[0][0].order_id
            il = map(lambda x: x[1], result)
            res = make_invoice(order, il)
            cr.execute('INSERT INTO sale_order_invoice_rel \
                    (order_id,invoice_id) values (%s,%s)', (order.id, res))

            flag = True
            data_sale = sales_order_obj.browse(cr, uid, line.order_id.id, context=context)
            for line in data_sale.order_line:
                if not line.invoiced:
                    flag = False
                    break
            if flag:
                if line.order_id.state != 'done':
                    sales_order_obj.write(cr, uid, [line.order_id.id], {'state': 'progress'})
                workflow.trg_validate(uid, 'sale.order', line.order_id.id, 'all_lines', cr)
           

        if not invoices:
            raise osv.except_osv(_('Warning'), _('Invoice cannot be created for this Sales Order Line due to one of the following reasons:\n1.The state of this sales order line is either "draft" or "cancel"!\n2.The Sales Order Line is Invoiced!'))

        cr.execute("SELECT p.id FROM stock_move AS m "
                   " INNER JOIN stock_picking AS p ON p.id = m.picking_id AND p.type = 'out' "
                   " WHERE m.sale_line_id IN %s "
                   " GROUP BY 1 ", (tuple(sale_line_ids),))
        
        picking_ids = [x[0] for x in cr.fetchall()]
        for picking in stock_picking_obj.browse(cr,uid,picking_ids,context):
            if picking.invoice_state == "2binvoiced":
                move_lines = picking.move_lines
                invoiced_count=0
                for move in picking.move_lines:
                    move_sale_line = move.sale_line_id
                    if move_sale_line and move_sale_line.invoiced:
                        invoiced_count+=1
                        
                #check if all are invoiced
                if invoiced_count==len(move_lines):
                    stock_picking_obj.write(cr,uid,picking.id,{"invoice_state":"invoiced"})
                
        
        return {'type': 'ir.actions.act_window_close'}

    _inherit = "sale.order.line.make.invoice"
    _columns = {
        "group" : fields.boolean("Group by Partner"),
    }
