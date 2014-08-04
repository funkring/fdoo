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

class posix_domain(osv.Model):
    
    def _get_mail_transport(self,cr,uid,ids,field_name,arg,context=None):
        cr.execute("SELECT d.id, d.mail_transport_type, d.mail_transport_host FROM posix_domain AS d WHERE d.id IN %s",(tuple(ids),))
        res = dict.fromkeys(ids)
        for row in cr.fetchall():
            transp_type = row[1]
            transp_host = row[2]            
            if transp_type and transp_type == "local:":
                res[row[0]]="%s%s" % (transp_type,transp_host)
            else:
                res[row[0]]=transp_type
        return res
                
          
    _inherit = "posix.domain"    
    _columns = {
        "mail_domain" : fields.boolean("Mail Domain"),      
        "mail_transport_type" : fields.selection([("virtual:","Virtual Mailbox Domain"),("relay:","Mail Relay"),("smtp:","Smtp Transport"),("local:","Local Transport")],"Mail Transport Type"),
        "mail_transport_host" : fields.char("Host",size=64),
        "mail_transport" :  fields.function(_get_mail_transport,string="Transport",type="char",size=72,store=True)        
    }        


class posix_alias(osv.Model):
    def _get_email(self, cr, uid, ids, field_name, arg, context=None):
        cr.execute("SELECT a.id, a.alias, d.complete_name FROM posix_mailalias AS a "
                   " INNER JOIN posix_domain d ON d.id = a.domain_id "
                   " WHERE a.id IN %s ",(tuple(ids),))
        res = dict.fromkeys(ids)
        for row in cr.fetchall():         
            alias_id = row[0] 
            user_alias = row[1]
            user_domain = row[2]
            email = None
            
            if user_alias and user_domain:
                email=("%s@%s" % (user_alias,user_domain))
            
            res[alias_id]=email
        return res
    
    _name = "posix.mailalias"
    _description = "Mail Alias"
    _columns = {
        "group_id" : fields.many2one("res.groups",string="Group",ondelete="cascade"),
        "user_id" : fields.many2one("res.users",string="User",ondelete="cascade"),        
        "domain_id" : fields.many2one("posix.domain",string="Domain",required=True,ondelete="restrict"),
        "domain_name" : fields.related("domain_id","complete_name",string="Domain",type="char",size=64,store=True),
        "alias" : fields.char("Alias",size=64,required=True),        
        "email" : fields.function(_get_email,string="E-mail",type="char",size=128,store=True,readonly=True,select=True),
    }


class posix_forward(osv.Model):    

    def _get_email(self, cr, uid, ids, field_names, arg, context=None):
        cr.execute("SELECT f.id, f.from_name, from_d.complete_name, f.to_name, to_d.complete_name FROM posix_mailforward AS f " 
                   "    LEFT JOIN posix_domain AS from_d ON from_d.id = f.from_domain_id "
                   "    LEFT JOIN posix_domain AS to_d ON to_d.id = f.to_domain_id "                   
                   " WHERE f.id IN %s",(tuple(ids),))
        res = dict.fromkeys(ids)
        for row in cr.fetchall():
            forward_id = row[0]         
            from_name = row[1]
            from_domain = row[2]
            to_name = row[3]
            to_domain = row[4]
            
            from_mail = None
            to_mail = None
                      
            if from_name and from_domain:
                from_mail=("%s@%s" % (from_name,from_domain))
            elif not from_name and from_domain:
                from_mail=("@%s" % (from_domain,))
            
            if to_name and to_domain:
                to_mail=("%s@%s" % (to_name,to_domain))
                
            elif not to_name and to_domain:
                to_mail=("@%s" % (to_domain,))
            
            res[forward_id]={
                "from_email" : from_mail,
                "to_email" : to_mail
            }
        return res
    
    def _relids_from_domain(self, cr, uid, ids, context=None):
        forward_obj = self.pool.get("posix.mailforward")
        res = forward_obj.search(cr, uid, [("from_domain_id", "in", ids)])
        return res
    
    def _relids_to_domain(self, cr, uid, ids, context=None):
        forward_obj = self.pool.get("posix.mailforward")
        res = forward_obj.search(cr, uid, [("to_domain_id", "in", ids)])
        return res
        
    _name = "posix.mailforward"
    _description = "Mail Forward"
    _columns = {
        "from_name" : fields.char("From",size=64,required=False),
        "from_domain_id" : fields.many2one("posix.domain",string="From Domain",required=True,ondelete="restrict"),
        "from_domain_name" : fields.related("from_domain_id","complete_name",string="From Domain",type="char",size=64,store=True),        
        "to_name" : fields.char("To",size=64,required=False),
        "to_domain_id" : fields.many2one("posix.domain",string="To Domain",required=True,ondelete="restrict"),
        "to_domain_name" : fields.related("to_domain_id","complete_name",string="To Domain",type="char",size=64,store=True),
        "from_email" : fields.function(_get_email,string="From E-Mail",type="char",size=128,readonly=True,select=True,multi="email",store={            
            "posix.mailforward": (lambda self, cr, uid, ids, context=None: ids, ["from_name","from_domain_id"],10),
            "posix.domain" :(_relids_from_domain, ["name", "parent_id"], 11)
        }),        
        "to_email" :fields.function(_get_email,string="To E-Mail",type="char",size=128,readonly=True,select=True,multi="email",store={            
            "posix.mailforward": (lambda self, cr, uid, ids, context=None: ids, ["to_name","to_domain_id"],10),
            "posix.domain" :(_relids_to_domain, ["name", "parent_id"], 11)
        })
        
    }


class res_group(osv.Model):    
    _inherit =  "res.groups"
    _columns = {       
        "posix_alias_ids" : fields.one2many("posix.mailalias","group_id","Aliases")
    }


class res_user(osv.Model):
    
    def copy_data(self, cr, uid, oid, default=None, context=None):
        if not default:
            default = {}
        
        if not default.has_key("posix_email"):
            default["posix_email"]=None
        if not default.has_key("posix_alias_ids"):
            default["posix_alias_ids"]=None
            
        res = super(res_user, self).copy_data(cr, uid, oid, default, context)
        
        return res
    
    def _posix_email(self, cr, uid, ids, field_name, arg, context=None):
        mailalias_obj = self.pool.get("posix.mailalias") 
        domain_obj = self.pool.get("posix.domain")
        cr.execute("SELECT u.id, u.posix, u.login, u.posix_domain_id FROM res_users AS u WHERE u.id IN %s",(tuple(ids),))
        res = dict.fromkeys(ids)
        for row in cr.fetchall():
            user_id = row[0]
            user_posix = row[1]
            user_login = row[2]
            user_domain = None
            user_domain_id = row[3]
            if user_domain_id:
                domain = domain_obj.browse(cr, uid, user_domain_id)
                user_domain = domain.complete_name
            user_email = None
            
            if user_posix and user_domain and user_login:     
                user_login = user_login.split("@")[0]           
                user_email=("%s@%s" % (user_login,user_domain))
                ids = mailalias_obj.search(cr,uid,[("alias","=",user_login),("user_id","=",user_id),("domain_id","=",user_domain_id)])
                if not ids:
                    mailalias_obj.create(cr,uid,{
                                "user_id" : user_id,
                                "domain_id" : user_domain_id,
                                "alias" : user_login
                            })                   
            
            res[user_id]=user_email
        return res
    
    def _relids_posix_domain(self, cr, uid, ids, context=None):
        user_obj = self.pool.get("res.users")
        res = user_obj.search(cr, uid, [("posix_domain_id", "in", ids)])
        return res
    
    _inherit = "res.users"
    _columns = {                
        "posix_email" : fields.function(_posix_email,string="E-mail",size=128, type="char",readonly=True,
                                        store={"posix.domain" :(_relids_posix_domain, ["name", "parent_id"], 10),
                                               "res.users" :  (lambda self, cr, uid, ids, context=None: ids, ["posix_email","login","posix_domain_id"], 10) }),  
        "posix_alias_ids" : fields.one2many("posix.mailalias","user_id","Aliases")
    }    
