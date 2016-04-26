import logging

from passlib.context import CryptContext

import openerp
from openerp.osv import fields, osv

from openerp.addons.base.res import res_users
res_users.USER_PRIVATE_FIELDS.append('password_crypt')

_logger = logging.getLogger(__name__)

default_crypt_context = CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
    ['pbkdf2_sha512', 'md5_crypt'],
    # deprecated algorithms are still verified as usual, but ``needs_update``
    # will indicate that the stored hash should be replaced by a more recent
    # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
    # algorithm but the default, but Debian only provides 1.5 so...
    deprecated=['md5_crypt'],
)

class res_users(osv.osv):
    _inherit = "res.users"

    _columns = {
        'password_crypt2': fields.char(string='Encrypted Password', invisible=True, copy=False)
    }
    
    def init(self, cr):
        cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='res_users' and column_name='password_crypt'")
        cr_res = cr.fetchone()
        if cr_res and cr_res[0] == "password_crypt":
            cr.execute("UPDATE res_users SET password_crypt2 = password_crypt")

    def check_credentials(self, cr, uid, password):
        # convert to base_crypt if needed
        cr.execute('SELECT password, password_crypt2 FROM res_users WHERE id=%s AND active', (uid,))
        encrypted = None
        if cr.rowcount:
            stored, encrypted = cr.fetchone()
            if stored and not encrypted:
                return super(res_users, self).check_credentials(cr, uid, password)
        try:
            return super(res_users, self).check_credentials(cr, uid, password)
        except openerp.exceptions.AccessDenied:
            if encrypted:
                valid_pass, replacement = self._crypt_context(cr, uid, uid)\
                        .verify_and_update(password, encrypted)
                if valid_pass:
                    self.write(cr, uid, uid, {"password" : password, "password_crypt2" : None})                    
                    return

            raise

    def _crypt_context(self, cr, uid, id, context=None):
        """ Passlib CryptContext instance used to encrypt and verify
        passwords. Can be overridden if technical, legal or political matters
        require different kdfs than the provided default.

        Requires a CryptContext as deprecation and upgrade notices are used
        internally
        """
        return default_crypt_context


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
