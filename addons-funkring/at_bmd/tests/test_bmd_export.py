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

class TestBmdExport(TransactionCase):
    """Test BMD Export"""
  
    def test_bmd_export_bmd55(self):
        taskc = TaskLogger("test_bmd_export")
        export = self.env.ref("at_bmd.demo_bmd_export")
        export._run(taskc)
        
        lines = export.line_ids
        self.assertEqual(len(lines), 7, "Check exported lines")
        
        buerf = self.env["bmd.export.file"].search([("bmd_export_id","=",export.id),
                                            ("export_name","=","buerf")], limit=1)
        
        self.assertTrue(buerf, "Check if buerf file was created")
        
        stamerf = self.env["bmd.export.file"].search([("bmd_export_id","=",export.id),
                                            ("export_name","=","stamerf")], limit=1)
        
        self.assertTrue(stamerf, "Check if stamerf file was created")
        
        self.env["util.test"]._testDownloadAttachments(export)
        
    def test_bmd_export_ntsc(self):
        taskc = TaskLogger("test_bmd_export")        
        export = self.env.ref("at_bmd.demo_bmd_export")
        export.profile_id.version = "ntcs"
        export._run(taskc)
        
        lines = export.line_ids
        self.assertEqual(len(lines), 7, "Check exported lines")
        
        buerf = self.env["bmd.export.file"].search([("bmd_export_id","=",export.id),
                                            ("export_name","=","buerf")], limit=1)
        
        self.assertTrue(buerf, "Check if buerf file was created")
        
        stamerf = self.env["bmd.export.file"].search([("bmd_export_id","=",export.id),
                                            ("export_name","=","stamerf")], limit=1)
        
        self.assertTrue(stamerf, "Check if stamerf file was created")
        
        self.env["util.test"]._testDownloadAttachments(export, prefix="ntcs-")
        
    def test_dist_export(self):
        taskc = TaskLogger("test_bmd_export")        
        export = self.env["bmd.export"].search([], limit=1)
        if not export:
            return
        
        export._run(taskc)        
        buerf = self.env["bmd.export.file"].search([("bmd_export_id","=",export.id),
                                            ("export_name","=","buerf")], limit=1)
        
        self.assertTrue(buerf, "Check if buerf file was created")
        
        stamerf = self.env["bmd.export.file"].search([("bmd_export_id","=",export.id),
                                            ("export_name","=","stamerf")], limit=1)
        
        self.assertTrue(stamerf, "Check if stamerf file was created")
        
        self.env["util.test"]._testDownloadAttachments(export)
        