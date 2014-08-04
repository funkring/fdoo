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
from at_base import util
import os
import tempfile
import netsvc

class mail_wizard(osv.osv_memory):
    """
    Mail Send Wizard
    """
    _name = "at_mail_wizard.mail_wizard"
    _description = "Mail Send Wizard"
              
    def action_send_mail(self,cr,uid,ids,context):
        if context:
            active_ids = context.get("active_ids",None)
            active_model = context.get("active_model",None)            
            if active_ids and active_model and ids:
                mail = self.browse(cr, uid, ids[0],context)

                cleanname = util.cleanFileName(mail.report_name)
                tmpfile =  os.path.join(tempfile.gettempdir(),cleanname + ".pdf")
                service = netsvc.LocalService("report."+mail.report_id.report_name)
                (result,format) = service.create(cr,uid,active_ids,{"model" : active_model },context)
                fp = open(tmpfile,"wb+")
                fp.write(result)
                fp.close()
               
                server_obj = self.pool.get("email.smtpclient") 
                for to_addr in mail.to.split(","):
                    if not  server_obj.send_email(cr,uid,
                                                  mail.smtp_server_id.id,
                                                  to_addr,
                                                  mail.subject,
                                                  mail.message,
                                                  [tmpfile],
                                                  context=context):
                        
                        raise osv.except_osv(_("Error"), _("Unable to send mail to %s") % to_addr)              
                         
        return { 'type': 'ir.actions.act_window_close' }
    
    
    def default_get(self, cr, uid, fields_list, context=None):
        res = super(mail_wizard,self).default_get(cr,uid,fields_list,context)        
        if context:
            active_ids = context.get("active_ids",None)
            active_model = context.get("active_model",None)
            report_name = context.get("report_name",active_model)            
            if active_ids and active_model:
                                
                if "report_id" in fields_list:
                    report_obj = self.pool.get("ir.actions.report.xml")
                    report_ids =report_obj.search(cr,uid,[('report_name','=',report_name)],context=context)                    
                    if not report_ids:
                        raise osv.except_osv(_("Warning"), _("No report named %s") % active_model)                    
                    res["report_id"] = report_ids[0]

                active_obj = self.pool.get(active_model)                
                if not hasattr(active_obj,"prepare_email"):
                    raise osv.except_osv(_("Warning"), _("prepare_email function not implemented in %s") % active_model)                    
               
                mail_prepares = active_obj.prepare_email(cr,uid,active_ids,context)                
                address_obj = self.pool.get("res.partner.address")
                
                cur_partner_id = None                
                cur_subject = []
                cur_mailAddresses = []
                cur_names = []
                
                for mail_prep in mail_prepares:                    
                    partner_id = mail_prep["partner_id"]
                    address_ids = mail_prep["address_ids"]
                    subject = mail_prep["subject"]
                    name = mail_prep["name"]
                    
                    cur_names.append(name)                
                        
                    if cur_partner_id and partner_id != cur_partner_id:
                        raise osv.except_osv(_('Warning'), _("Different Partner are used"))
                    
                    cur_partner_id = partner_id
                    if subject:
                        cur_subject.append(subject)
                                                                    
                    for address in address_obj.browse(cr,uid,address_ids):
                        if address.email and address.email not in cur_mailAddresses:
                            cur_mailAddresses.append(address.email)
                    
                  
                if "subject" in fields_list:   
                    res["subject"] =",".join(cur_subject)
                    
                if "to" in fields_list:
                    res["to"] = ",".join(cur_mailAddresses)
                    
                if "report_name" in fields_list:
                    res["report_name"] = "_".join(cur_names)   
                    
                if "smtp_server_id" in fields_list:
                    smtp_server_obj = self.pool.get("email.smtpclient")
                    smtp_server_ids = smtp_server_obj.search(cr, uid, [('type','=','default'),('state','=','confirm'),('active','=',True)], context=False)
                    if not smtp_server_ids:
                        raise osv.except_osv(_("Warning"), _("No SMTP Server defined"))                    
                    res["smtp_server_id"] = smtp_server_ids[0]
                    
                if "message" in fields_list:
                    user = self.pool.get('res.users').browse(cr, uid, uid, context)
                    if user.signature:
                        res["message"] = "\n--\n" + user.signature                    
                           
            else:
                raise osv.except_osv(_("Warning"), _("Nothing Selected"))
                
        return res      
        
    
    _columns = {
        "to" : fields.char("To",size=1024,required=True),
        "subject" : fields.char("Subject",size=255,required=True),
        "message" : fields.text("Message", required=True),
        "report_id" : fields.many2one("ir.actions.report.xml","Report",required=True),
        "smtp_server_id" : fields.many2one("email.smtpclient","Smtp Server",required=True),
        "report_name" : fields.text("Report Name", required=True)
                
    }
mail_wizard()