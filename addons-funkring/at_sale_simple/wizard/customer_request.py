#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martinr@funkring.net>
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

class customer_request(osv.osv_memory):
    _name = "at_sale_simple.wizard.customer_request"   
    _description = "A new customer request"    
    _columns = {
        "partner_address_id" : fields.many2one("res.partner.address","Contact"),
        'title': fields.many2one('res.partner.title','Title'),
        'name': fields.char('Contact Name', size=64, select=1),
        'street': fields.char('Street', size=128),
        'street2': fields.char('Street', size=128),
        'zip': fields.char('Zip', change_default=True, size=24),
        'city': fields.char('City', size=128),
        'state_id': fields.many2one("res.country.state", 'Fed. State', domain="[('country_id','=',country_id)]"),
        'country_id': fields.many2one('res.country', 'Country'),
        'email': fields.char('E-Mail', size=240),
        'phone': fields.char('Phone', size=64),
        'fax': fields.char('Fax', size=64),
        'mobile': fields.char('Mobile', size=64),      
        'has_delivery_address' : fields.boolean("Delivery address",help="Delivery address is not the same as accounting address"),  
        'delivery_name': fields.char('Contact Name', size=64, select=1),
        'delivery_street': fields.char('Street', size=128),        
        'delivery_street2': fields.char('Street2', size=128),
        'delivery_zip': fields.char('Zip', change_default=True, size=24),
        'delivery_city': fields.char('City', size=128),
        'delivery_state_id': fields.many2one("res.country.state", 'Fed. State', domain="[('country_id','=',country_id)]"),
        'delivery_country_id': fields.many2one('res.country', 'Country'),
        'ref_person_title': fields.many2one('res.partner.title','Title'),
        'ref_person_name': fields.char('Contact', size=64, select=1),
        'ref_person_email': fields.char('E-Mail', size=240),
        'ref_person_phone': fields.char('Phone', size=64),
        'ref_person_fax': fields.char('Fax', size=64),
        'ref_person_mobile': fields.char('Mobile', size=64),
    }
    
    def on_change_zip(self, cr, uid, ids, inZip):
        res = {}
        tCity = self.pool.get("res.partner.address").city_search(cr,uid,inZip)
        if tCity:
            res["value"] = { "city" : tCity }
                        
        return res
    
    def on_change_delivery_zip(self, cr, uid, ids, inZip):
        res = {}
        tCity = self.pool.get("res.partner.address").city_search(cr,uid,inZip)
        if tCity:
            res["value"] = { "delivery_city" : tCity }
                        
        return res
    
    def action_create(self, cr, uid, ids, context=None):
        """ returns the partner id or create a new 
            prospective customer 
        @return:  res.partner.address id    
        """
                        
        address_obj = self.pool.get("res.partner.address")
        request = self.browse(cr, uid, ids[0], context);      
        partner_address = request.partner_address_id                
      
        if not partner_address:
            partner_obj = self.pool.get("res.partner")
            partner_id = partner_obj.create(cr,uid, {
                'name' : request.name,
                'prospective_customer' : True,
                'customer' : False,
                'supplier' : False
            })
            
            partner_address_id = address_obj.create(cr,uid, {
                'partner_id' : partner_id,                
                'type' : 'default',                
                'name' : request.name,
                'title' : request.title and request.title.id or None,
                'street' : request.street,
                'street2' : request.street2,
                'zip' : request.zip,
                'city' : request.city,
                'state_id' : request.state_id and request.state_id.id or None,
                'country_id' : request.country_id and request.country_id.id or None,
                'email' : request.email,
                'phone' : request.phone,
                'mobile' : request.mobile,
                'fax' :request.fax,                                                                     
            })
            
            if request.ref_person_name:
                address_obj.create(cr,uid, {
                    'partner_id' : partner_id,
                    'type' : 'contact',
                    'title' : request.ref_person_title and request.ref_person_title.id or None,
                    'name' : request.ref_person_name,
                    'email' : request.ref_person_email,
                    'phone' : request.ref_person_phone,
                    'fax' : request.ref_person_fax,
                    'mobile' : request.ref_person_mobile
                    
            })                                                   
                
            
            partner_address = address_obj.browse(cr,uid,partner_address_id)        
            
        if partner_address:            
            if request.has_delivery_address:
                return address_obj.create(cr,uid, {
                    'partner_id' : partner_address.partner_id.id,
                    'type' : 'delivery',
                    'name' : request.delivery_name,                    
                    'street' : request.delivery_street,
                    'street2' : request.delivery_street2,
                    'zip' : request.delivery_zip,
                    'city' : request.delivery_city,
                    'state_id' : request.delivery_state_id and request.delivery_state_id.id or False,
                    'delivery_country_id' : request.delivery_country_id and request.delivery_country_id.id or False                    
                    } )                
                
            return partner_address.id
            
        raise osv.except_osv(_("Error!"), _("Cannot create new address"))        
    
    def action_cancel(self, cr, uid, ids, context=None):
        return { "type" : "ir.actions.act_window_close" }
    
    def action_create_phone_call(self, cr, uid, ids, context={}):
        address_obj = self.pool.get("res.partner.address")        
        address = address_obj.browse(cr,uid,self.action_create(cr, uid, ids, context))
        
        context['default_partner_id'] = address.partner_id.id or False            
        context['default_partner_address_id'] = address.id
        
        return {
            "name" : _("New Phone Call"),
            "view_type" : "form",
            "view_mode" : "form,tree",
            "res_model" : "crm.phonecall",
            "context" : context,
            "type" : "ir.actions.act_window"
        }
        
    
    def action_create_opportunity(self, cr, uid, ids, context={}):
        address_obj = self.pool.get("res.partner.address")        
        address = address_obj.browse(cr,uid,self.action_create(cr, uid, ids, context))
        
        context['default_partner_id'] = address.partner_id.id or False            
        context['default_partner_address_id'] = address.id
        context['default_type'] = 'opportunity'
                
        return {
            "name" : _("New Customer Opportunity"),
            "view_type" : "form",
            "view_mode" : "form,tree",
            "res_model" : "crm.lead",
            "context" : context,
            "type" : "ir.actions.act_window"
        }        
    
    
    def action_create_sale_order(self, cr, uid, ids, context={}):
        address_obj = self.pool.get("res.partner.address")    
               
        address = address_obj.browse(cr,uid,self.action_create(cr, uid, ids, context))
        context['default_partner_id'] = address.partner_id.id or False
        context['default_partner_shipping_id'] = address.id
        
        return {
            "name" : _("New Sale Order"),
            "view_type" : "form",
            "view_mode" : "form,tree",
            "res_model" : "sale.order",
            "context" : context,
            "type" : "ir.actions.act_window"        
        }       
customer_request() 
        