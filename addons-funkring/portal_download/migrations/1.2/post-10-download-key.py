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

__name__ = ("Add Download Key")

import uuid

def migrate(cr, version):
    if not version:
        return
    
    cr.execute("SELECT id FROM portal_download_perm WHERE download_key IS NULL")
    ids = [r[0] for r in cr.fetchall()]
    
    for perm_id in ids:
         cr.execute("UPDATE portal_download_perm SET download_key = '%s' WHERE id = %s" % (uuid.uuid4().hex, perm_id))