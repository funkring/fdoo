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

from openerp.osv import fields, osv

class academy_invoice_assistant(osv.osv_memory):

    _name = "academy.invoice.assistant"

    def action_offset(self, cr, uid, ids, context=None):
        invoice_obj = self.pool["account.invoice"]
        invoice_line_obj = self.pool["account.invoice.line"]
        registration_obj = self.pool["academy.registration"]
        reg_inv_obj = self.pool["academy.registration.invoice"]

        for wizard in self.browse(cr, uid, ids, context=context):
            value = {}
            semester = wizard.semester_id

            for registration in wizard.registration_ids:
                registrations = {}
                if registration.semester_id.id == semester.id:
                    address_id = registration.use_invoice_address_id.id
                    registrations["product"] = registration.course_prod_id.product_id
                    registrations["rent_product_id"] = registration.location_id.rent_product_id.id
                    registrations["amount"] = registration.amount
                    registrations["id"] = registration.id
                    registrations["account_id"] = registration.use_invoice_address_id.property_account_receivable.id
                    if value.get(address_id):
                        value[address_id].append(registrations)
                    else:
                        value[address_id] = [registrations]

        for address_id, registrations in value.iteritems():
            used_rent_product_ids = []
            invoice_id = None

            for registration in registrations:
                reg_inv_ids = reg_inv_obj.search(cr, uid, [("registration_id", "=", registration["id"]), ("semester_id", "=", semester.id)], context=context)
                if not reg_inv_ids:
                    if not invoice_id:
                        invoice_id = invoice_obj.create(cr, uid, {"partner_id" : address_id,
                                                                  "account_id" : registration["account_id"],
                                                                  "type" : "out_invoice"})
                    rent_product_id = registration["rent_product_id"]
                    if rent_product_id and rent_product_id not in used_rent_product_ids:
                        invoice_line_obj.create(cr, uid, {"product_id" : rent_product_id,
                                                          "invoice_id" : invoice_id})
                        used_rent_product_ids.append(rent_product_id)
                    invoice_line_obj.create(cr, uid, {"product_id" : registration["product"].id,
                                                      "name" : registration["product"].name,
                                                      "amount" : registration["amount"],
                                                      "invoice_id" : invoice_id})
                    reg_inv_obj.create(cr, uid, {"registration_id" : registration["id"],
                                                 "semester_id" : semester.id,
                                                 "invoice_id" : invoice_id})

            invoice_obj.button_compute(cr, uid, [invoice_id])

    def _get_registration_ids(self, cr, uid, context=None):
        return context.get("active_ids")

    _columns = {
        "semester_id" : fields.many2one("academy.semester", "Semester", required=True),
        "registration_ids" : fields.many2many("academy.registration", "academy_registration_wizard_rel", "registration_id", "wizard_id", "Registrations to offset"),
        "customer_ref" : fields.char("Reference")
    }

    _defaults = {
        "registration_ids" : _get_registration_ids
    }

















