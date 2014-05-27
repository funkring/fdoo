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

from openerp.osv import fields

class duplicate(fields.function):
    def _fnct_search(self, tobj, cr, uid, obj=None, name=None, domain=None, context=None):
        return []

    def _fnct_write(self, obj, cr, uid, ids, field_name, values, args, context=None):
        return False

    def _fnct_read(self, obj, cr, uid, ids, field_name, arg, context=None):
        values =  obj.read(cr,uid,ids,[arg],context)
        res = dict.fromkeys(ids)
        for value in values:
            res[value["id"]]=value[arg]
        return res        

    def __init__(self, orig, string, **args):
        self.arg = orig
        self._relations = []
        super(duplicate, self).__init__(self._fnct_read, orig, self._fnct_write, fnct_inv_arg=orig, string=string, method=True, fnct_search=None, **args)

