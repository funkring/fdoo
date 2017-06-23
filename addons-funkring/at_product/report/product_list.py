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

from openerp.addons.at_base import extreport

class Parser(extreport.basic_parser):
    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            "prepare": self._prepare
        })
        
    def _prepare(self, objects):
        if not objects:
            return []
        
        product_obj = self.pool["product.product"]
        ids = [o.id for o in objects]
        
        if objects[0]._model._name == "product.template":
            self.cr.execute("SELECT pt.id, p.id FROM product_template pt "
                 " INNER JOIN product_product p ON p.product_tmpl_id = pt.id "
                 " WHERE pt.id IN %s ORDER BY 1 ",(tuple(ids),))
            
            ids = [r[1] for r in self.cr.fetchall()]

        return product_obj._product_overview(self.cr, self.uid, ids, context=self.localcontext)
        

        