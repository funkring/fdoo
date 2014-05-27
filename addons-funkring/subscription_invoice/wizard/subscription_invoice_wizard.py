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
from openerp.tools.translate import _

def _get_document_types(self, cr, uid, context=None):
    cr.execute("select m.model, m.name from subscription_document s, ir_model m WHERE s.model = m.id GROUP BY 1,2")
    return cr.fetchall()

class subscription_invoice_wizard(osv.osv_memory):
    
    def apply(self, cr, uid, ids, context=None):
        
        subscription_obj = self.pool.get("subscription.subscription")
        
        for wizard in self.browse(cr, uid, ids):
            
            subscription_id = int(wizard.subscription_id)
            subscription_obj.write(cr, uid, [subscription_id], {
                                        "name" : wizard.name,
                                        "interval_number": wizard.interval_number,
                                        "interval_type": wizard.interval_type,
                                        "exec_init": wizard.exec_init,
                                        "date_init": wizard.date_init,
                                        "doc_source": "account.invoice,"+str(wizard.doc_source.id),
                                        "doc_id" : wizard.doc_id.id,
                                    }, context)
            if wizard.state == "draft":
                subscription_obj.set_draft(cr, uid, [subscription_id], context)
                
            elif wizard.state == "running":
                subscription_obj.set_process(cr, uid, [subscription_id], context)
                
            elif wizard.state == "done":
                subscription_obj.set_done(cr, uid, [subscription_id], context)
                
            self.unlink(cr, uid, [wizard.id], context)
            
        return {"type" : "ir.actions.act_window_close"}
    
    def set_process(self, cr, uid, ids, context=None):
        
        self.write(cr, uid, ids, {"state" : "running"})        
        
        obj_model = self.pool.get("ir.model.data")
        model_data_ids = obj_model.search(cr,uid,[("model","=","ir.ui.view"),("name","=","wizard_subscription_invoice4")])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=["res_id"])[0]["res_id"]

        return {
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "subscription.invoice_wizard",
            "views": [(resource_id,"form")],
            "res_id" : ids[0],
            "type": "ir.actions.act_window",
            "target" : "new",
            "context": context,
        }
    
    
    def set_done(self, cr, uid, ids, context=None):
        
        self.write(cr, uid, ids, {"state" : "done"}) 
               
        obj_model = self.pool.get("ir.model.data")
        model_data_ids = obj_model.search(cr,uid,[("model","=","ir.ui.view"),("name","=","wizard_subscription_invoice4")])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=["res_id"])[0]["res_id"]

        return {
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "subscription.invoice_wizard",
            "views": [(resource_id,"form")],
            "res_id" : ids[0],
            "type": "ir.actions.act_window",
            "target" : "new",
            "context": context,
        }
        
    def set_draft(self, cr, uid, ids, context=None):
        
        self.write(cr, uid, ids, {"state" : "draft"})        
        
        obj_model = self.pool.get("ir.model.data")
        model_data_ids = obj_model.search(cr,uid,[("model","=","ir.ui.view"),("name","=","wizard_subscription_invoice4")])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=["res_id"])[0]["res_id"]

        return {
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "subscription.invoice_wizard",
            "views": [(resource_id,"form")],
            "res_id" : ids[0],
            "type": "ir.actions.act_window",
            "target" : "new",
            "context": context,
        }
        
        
    def do_next(self, cr, uid, ids, context=None):
        
        for wizard in self.browse(cr, uid, ids):
            
            subscription_obj = self.pool.get("subscription.subscription")
            subscription_id = int(wizard.subscription_id)
            subscription = subscription_obj.browse(cr, uid, subscription_id)
            
            datas = {
                "name" : subscription.name,
                "interval_number": subscription.interval_number,
                "interval_type": subscription.interval_type,
                "exec_init": subscription.exec_init,
                "date_init": subscription.date_init,
                "doc_source": "account.invoice,"+str(subscription.doc_source.id),
                "doc_id" : subscription.doc_id.id,
                "state" : subscription.state
            }
            
            self.write(cr, uid, [wizard.id], datas)
            
            obj_model = self.pool.get("ir.model.data")
            model_data_ids = obj_model.search(cr,uid,[("model","=","ir.ui.view"),("name","=","wizard_subscription_invoice4")])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=["res_id"])[0]["res_id"]

            return {
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "subscription.invoice_wizard",
                "views": [(resource_id,"form")],
                "res_id" : ids[0],
                "type": "ir.actions.act_window",
                "target" : "new",
                "context": context,
            }
    
    
    def edit_existing(self, cr, uid, ids, context=None):
        
        if len(context.get("active_ids")) == 1: 
            obj_model = self.pool.get("ir.model.data")
            model_data_ids = obj_model.search(cr,uid,[("model","=","ir.ui.view"),("name","=","wizard_subscription_invoice3")])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=["res_id"])[0]["res_id"]
            
            return {
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "subscription.invoice_wizard",
                "views": [(resource_id,"form")],
                "type": "ir.actions.act_window",
                "target" : "new",
                "context": context,
        }
        else:
            raise osv.except_osv(_("Error!"), _("You have to select exactly 1 invoice!"))
        
    
    def create_new(self, cr, uid, ids, context=None):
        
        if len(context.get("active_ids")) == 1: 
            obj_model = self.pool.get("ir.model.data")
            model_data_ids = obj_model.search(cr,uid,[("model","=","ir.ui.view"),("name","=","wizard_subscription_invoice2")])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=["res_id"])[0]["res_id"]
            
            return {
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "subscription.invoice_wizard",
                "views": [(resource_id,"form")],
                "type": "ir.actions.act_window",
                "target" : "new",
                "context": context,
            }
        else:
            raise osv.except_osv(_("Error!"), _("You have to select exactly 1 invoice!"))
    
    
    def create_process(self, cr, uid, ids, context=None):
        
        for wizard in self.browse(cr, uid, ids):
            context["call_process"] = True
            self.create_subscription(cr, uid, ids, context)
            self.pool.get("subscription.subscription").set_process(cr, uid, [wizard.subscription_id], context)
            self.unlink(cr, uid, [wizard.id], context=context)
        return {"type" : "ir.actions.act_window_close"}

            
    def create_subscription(self, cr, uid, ids, context=None):
        
        subscription_obj = self.pool.get("subscription.subscription")
        
        for wizard in self.browse(cr, uid, ids):
            datas = {}
            
            datas["name"] = wizard.name
            datas["interval_number"] = wizard.interval_number
            datas["interval_type"] = wizard.interval_type
            datas["exec_init"] = wizard.exec_init
            datas["doc_source"] = str(wizard.doc_id.model.model)+","+str(wizard.doc_source.id)
            datas["doc_id"] = wizard.doc_id.id
            
            subscription_id = subscription_obj.create(cr, uid, datas, context=None)
            self.write(cr, uid, [wizard.id], {"subscription_id" : subscription_id})
            if not context.get("call_process"):
                self.unlink(cr, uid, [wizard.id], context=context)
        return {"type" : "ir.actions.act_window_close"}
            
            
    def _get_doc_source(self, cr, uid, context=None):
        value = "account.invoice,"+str(context.get("active_id"))
        return value
    
    def _get_source_model(self, cr, uid, context=None):
        return "account.invoice"
    
    
    _name = "subscription.invoice_wizard"
    
    _columns = {
        "name" : fields.char("Name", size=60),
        "interval_number": fields.integer("Interval Qty", help="This number indicates how often it will create the document. "
                                                               "If its set to 3, the document is created every third day, week or month, "
                                                               "depending on the interval."),
        "interval_type": fields.selection([("days", "Days"), ("weeks", "Weeks"), ("months", "Months")], "Intervall"),
        "exec_init": fields.integer("Number of Documents", help="This number indicates, how much documents should be created. "
                                                                "If its set to 10, then it will create 10 documents."),
        "date_init": fields.datetime("Begin"),
        "doc_source": fields.reference("Source Document", selection=_get_document_types, size=128,
                                       help="User can choose the source document on which he wants to create documents"),
        "doc_id" : fields.many2one("subscription.document", "Document type", help="Within the document type, the user can set the properties "
                                                                                       "for the document, which should be created."),
        "subscription_id" : fields.many2one("subscription.subscription", string="Subscription"),
        "state": fields.selection([("draft","Draft"),("running","Running"),("done","Done")], "State"),
        "doc_source_model" : fields.char("Doc source Model", size=32)
    }
    
    _defaults = {
        "doc_source" : _get_doc_source,
        "state": lambda *a: "draft",
        "doc_source_model" : _get_source_model
    }