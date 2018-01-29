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
from openerp import SUPERUSER_ID
from openerp.addons.at_base import util

class project_project(osv.Model):
    
    def _shop_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for prj in self.browse(cr, uid, ids, context):
            # take shop from order
            order = prj.order_id
            shop = None
            if order:
                shop=order.shop_id            
            # take user defined shop
            if not shop:
                shop = prj.user_shop_id

            # result
            if shop:
                res[prj.id] = shop.id
                 
        return res

    def onchange_shop_id(self, cr, uid, ids, user_shop_id, order_id, context=None):
        value = {}
        res = { "value" : value }
        
        if not order_id and user_shop_id:
            shop = self.pool["sale.shop"].browse(cr, uid, user_shop_id, context=context)
            proj_template = shop.project_template_id
            if proj_template:
                stage_ids = [s.id for s in proj_template.type_ids]
                
                member_ids = [m.id for m in proj_template.members]
                if member_ids and not uid in member_ids:
                    member_ids.append(uid)
                
                parent = proj_template.parent_id
                value["parent_id"] = parent and parent.id or None
                 
                value["type_ids"] = [(6,0,stage_ids)]
                value["privacy_visibility"] = proj_template.privacy_visibility
                value["color"] = proj_template.color
                
                value["members"] = [(6,0,member_ids)]
        
        return res
    
    def _default_shop_id(self, cr, uid, context=None):
        # check default shop from user
        shop_ref = self.pool["res.users"].read(cr, uid, uid, ["shop_id"], context=context)["shop_id"]
        if shop_ref:
            return shop_ref[0]
        
        # search based on company
        company_id = self.pool.get("res.company")._company_default_get(cr, uid, "project.project", context=context)
        res = None
        if company_id:
            shop_obj = self.pool.get("sale.shop")
            res = shop_obj.search_id(cr, uid, [("company_id","=",company_id)],context=context)
            if not res:
                res = shop_obj.search_id(cr, uid, [("company_id","=",False)],context=context)
        return res

    _inherit = "project.project"
    _columns = {
        "shop_id" : fields.function(_shop_id,type="many2one", relation="sale.shop", store=True, string="Shop"),
        "user_shop_id" : fields.many2one("sale.shop","Shop")
    }
    _defaults = {
        "user_shop_id" : _default_shop_id
    }
    

class project_task(osv.Model):
    
    def _relids_project(self, cr, uid, ids, context=None):
      return self.pool["project.task"].search(cr, SUPERUSER_ID, [("project_id","in",ids)], context={"active_test" : False})
      
    def _relids_sale_order(self, cr, uid, ids, context=None):
      cr.execute("SELECT t.id FROM sale_order o "  
                 " INNER JOIN project_project p ON p.analytic_account_id = o.project_id " 
                 " INNER JOIN project_task t ON t.project_id = p.id " 
                 " WHERE o.id IN %s "
                 " GROUP BY 1  ", (tuple(ids),))      
      task_ids = [r[0] for r in cr.fetchall()]
      return task_ids
    
    _inherit = "project.task"
    _columns = {
        "shop_id" : fields.related("project_id", "shop_id", type="many2one", relation="sale.shop", string="Shop",
                                   store={
                                      "sale.order": (_relids_sale_order,["shop_id"], 10),
                                      "project.project" : (_relids_project,["shop_id","user_shop_id"],10),
                                      "project.task": (lambda self, cr, uid, ids, context=None: ids, ["project_id"],10)
                                   })  
    }
    
    
class project_issue(osv.Model):
    
    def _relids_project(self, cr, uid, ids, context=None):
        return self.pool["project.issue"].search(cr, SUPERUSER_ID, [("project_id","in",ids)], context={"active_test" : False})
   
    def on_change_project_check_stage(self, cr, uid, ids, project_id, stage_id, context=None):
        if project_id:
            res = self.on_change_project(cr, uid, ids, project_id, context)
            project = self.pool.get('project.project').browse(cr, uid, project_id, context=context)
            
            # check stage
            stage_ids = [s.id for s in project.type_ids]
            next_stage_id = stage_id
            if stage_ids and (not stage_id or not next_stage_id in stage_ids):
                next_stage_id = stage_ids[0]

            # update stage
            if stage_id != next_stage_id:
                util.deepUpdate(res,{"value" : {"stage_id" : next_stage_id}})
                res_stage = self.onchange_stage_id(cr, uid, ids, next_stage_id, context=context)              
                util.deepUpdate(res, res_stage)                
            
            return res                
        return {}
    
    def assign_project(self, cr, uid, ids, project_id, context=None):
        res = self.on_change_project_check_stage(cr, uid, ids, project_id, None, context=context)
        
        values = res.get("value",None)
        if values is None:
            values = {}
            
        values["project_id"] = project_id
        self.write(cr, uid, ids, values, context=context)
        return True            
        
    
    _inherit = "project.issue"
    _columns = {
       "shop_id" : fields.related("project_id", "shop_id", type="many2one", relation="sale.shop", string="Shop",
                                   store={
                                       "project.project" : (_relids_project,["shop_id","user_shop_id"],10),
                                       "project.issue": (lambda self, cr, uid, ids, context=None: ids, ["project_id"],10)
                                   })  
    }