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

from openerp.tests.common import TransactionCase
from openerp.addons.automation.automation import TaskLogger

class TestBmdReconcile(TransactionCase):
    """Test BMD Reconcilation"""
  
    def test_bmd_reconcile(self):
        taskc = TaskLogger("test_bmd_export")        
        reconcil = self.env["bmd.reconcil"].search([], limit=1)
        if not reconcil:
            return
        
        reconcil._run(taskc)
        