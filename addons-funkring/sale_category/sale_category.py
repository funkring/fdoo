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

class sale_category(osv.osv):

    _name = "sale.category"
    _description = "Sale category"

    _columns = {
        "name" : fields.char("Name", size=64, required=True),
        "report_ids" : fields.one2many("sale.category.report", "category_id", "Report")
    }


class sale_category_report(osv.osv):

    _name = "sale.category.report"
    _description = "Sale category report"

    _columns = {
        "name" : fields.char("Name", size=64),
        "category_id" : fields.many2one("sale.category", "Category",on_delete="cascade",required=True),
        "source_report_id" : fields.many2one("ir.actions.report.xml", "Source Report",on_delete="cascade",required=True),
        "dest_report_id" : fields.many2one("ir.actions.report.xml", "Destination Report",on_delete="cascade",required=True),
    }


class report_xml(osv.osv):

    def _get_replacement(self, cr, uid, res_model, res_id, report_xml, context=None):
        model_obj =self.pool.get(res_model)
        res_br = model_obj.browse(cr,uid,res_id,context=context)
        if res_br and hasattr(res_br, "sale_category_id"):
            sale_category = res_br.sale_category_id
            if sale_category:
                report_obj = self.pool.get("sale.category.report")
                report_ids = report_obj.search(cr, uid, [("category_id","=",sale_category.id),("source_report_id","=",report_xml.id)])
                if report_ids:
                    report = report_obj.browse(cr, uid, report_ids[0], context=context)
                    return report.dest_report_id
        return None

    _inherit = "ir.actions.report.xml"
