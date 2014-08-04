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

POSTFIX_USER = "mailproc"

class postfix_transport(osv.Model):
    _name = "postfix.transport"
    _description = "Postfix Transport Table"
    _auto = False
    _columns = {
        "domain" : fields.char("Domain",size=64),
        "transport" : fields.char("Transport",size=72)
    }
    
    def init(self,cr):
        cr.execute("SELECT COUNT(usename) FROM pg_user WHERE usename=%s",(POSTFIX_USER,))
        for row in cr.fetchall():
            if not row[0]:
                cr.execute("CREATE USER " + POSTFIX_USER)
        
        cr.execute(
        """
        CREATE OR REPLACE VIEW postfix_transport AS (
            SELECT d.complete_name AS domain,'virtual:' AS transport FROM posix_domain AS d WHERE d.mail_domain=True
        ) """)        
        cr.execute("GRANT SELECT ON postfix_transport TO " + POSTFIX_USER)        
        cr.execute("GRANT SELECT ON res_users TO " + POSTFIX_USER)        


class postfix_users(osv.Model):
    _name = "postfix.users"
    _description = "Postfix User Table"
    _auto = False
    _columns =  {
        "userid" : fields.char("User",size=128),
        "email" : fields.char("E-Mail",size=128),        
        "home" : fields.char("Home",size=128)
    }
    
    def init(self,cr):
        cr.execute(
        """
        CREATE OR REPLACE VIEW postfix_users AS (
            SELECT u.login AS userid, u.posix_email AS email, u.login AS home FROM res_users AS u
            INNER JOIN posix_domain AS d ON d.id = u.posix_domain_id AND d.mail_domain = True  
            WHERE u.posix_email IS NOT NULL          
        )""")        
        cr.execute("GRANT SELECT ON postfix_users TO " + POSTFIX_USER)


class postfix_mailbox(osv.Model):
    _name = "postfix.mailbox"
    _description = "Postfix Mailbox"
    _auto = False
    _columns =  {
        "userid" : fields.char("User",size=128),
        "mailbox" : fields.char("Home",size=128)
    }
    
    def init(self,cr):
        cr.execute(
        """        
        CREATE OR REPLACE VIEW postfix_mailbox AS (
            SELECT u.login AS userid, u.login AS mailbox FROM res_users AS u
            INNER JOIN posix_domain AS d ON d.id = u.posix_domain_id AND d.mail_domain = True  
            WHERE u.posix_email IS NOT NULL
        UNION ALL
            SELECT d.name AS userid, 'dummy' AS mailbox FROM posix_domain AS d WHERE d.mail_domain=True
        ) 
        """)
        cr.execute("GRANT SELECT ON postfix_mailbox TO " + POSTFIX_USER)


class postfix_user_alias(osv.Model):
    _name = "postfix.user.alias"
    _description = "Postfix User Alias Table"
    _auto = False
    _columns =  {
        "alias" : fields.char("Alias",size=128),
        "email" : fields.char("E-Mail",size=128)
    }
    
    def init(self,cr):
        cr.execute(
       """
        CREATE OR REPLACE VIEW postfix_user_alias AS (
            SELECT a.email AS alias, u.posix_email AS email FROM posix_mailalias AS a
            INNER JOIN res_users AS u ON u.id = a.user_id
            INNER JOIN posix_domain AS d1 ON d1.id = u.posix_domain_id AND d1.mail_domain = True
            INNER JOIN posix_domain AS d2 ON d2.id = a.domain_id AND d2.mail_domain = True  
            WHERE a.email IS NOT NULL AND u.posix_email IS NOT NULL GROUP BY 1,2       
        ) """)    
        cr.execute("GRANT SELECT ON postfix_user_alias TO " + POSTFIX_USER)


class postfix_group_alias(osv.Model):
    _name = "postfix.group.alias"
    _description = "Postfix Group Alias Table"
    _auto = False
    _columns =  {
        "alias" : fields.char("Alias",size=128),
        "email" : fields.char("E-Mail",size=128)
    }
    
    def init(self,cr):
        cr.execute(
        """
        CREATE OR REPLACE VIEW postfix_group_alias AS (
            SELECT a.email AS alias, u.posix_email AS email FROM posix_mailalias AS a
            INNER JOIN res_groups AS g ON g.id = a.group_id
            INNER JOIN res_groups_users_rel AS grel ON grel.gid = a.group_id
            INNER JOIN res_users AS u ON u.id = grel.uid
            INNER JOIN posix_domain AS d1 ON d1.id = g.posix_domain_id AND d1.mail_domain = True
            INNER JOIN posix_domain AS d2 ON d2.id = a.domain_id AND d2.mail_domain = True
            WHERE a.email IS NOT NULL AND u.posix_email IS NOT NULL GROUP BY 1,2
        ) """)       
        cr.execute("GRANT SELECT ON postfix_group_alias TO " + POSTFIX_USER) 


class postfix_alias(osv.Model):
    _name = "postfix.alias"
    _description = "Postfix Alias Table"
    _auto = False
    _columns =  {
        "alias" : fields.char("Alias",size=128),
        "email" : fields.char("E-Mail",size=128)
    }
    
    def init(self,cr):
        cr.execute(
         """
         CREATE OR REPLACE VIEW postfix_alias AS (
             SELECT alias, email FROM postfix_group_alias 
             UNION ALL
             SELECT from_email AS alias, to_email AS email FROM posix_mailforward 
             UNION ALL
             SELECT alias, email FROM postfix_user_alias
             )
         """)
        cr.execute("GRANT SELECT ON postfix_alias TO " + POSTFIX_USER)
