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
import util
import re

class res_partner_title(osv.Model):
    _inherit = "res.partner.title"
    _columns = {
        "mail_salutation": fields.text("Mail Salutation",translate=True),
        "co_salutation" : fields.text("C/O Salutation",translate=True),
        "active" : fields.boolean("Active")
    }
    _defaults = {
        "active" : True
    }

class res_partner(osv.osv):

    def _check_for_ref(self,cr,uid,vals,context=None):
        if not vals.get("ref",False) and (vals.get("customer",False) or vals.get("supplier",False)):
            vals["ref"]=self.pool.get('ir.sequence').get(cr, uid, 'res.partner')

    def write(self, cr, uid, ids, vals, context=None):
        # check if name, surname or firstname are changed
        has_name = vals.get("name")
        if not has_name and ("surname" in vals or "firstname" in vals):
            # generate name for each
            for partner_vals in self.read(cr, uid, ids, ["name","is_company","surname","firstname"]):
                if not vals.get("is_company",partner_vals.get("is_company")):
                    name_build = []
                    last_name = vals.get("surname", partner_vals.get("surname"))
                    if last_name:
                        name_build.append(last_name)
                    first_name = vals.get("firstname", partner_vals.get("firstname"))
                    if first_name:
                        name_build.append(first_name)
                    name = vals.get("name")
                    new_vals = vals.copy()
                    if name_build:
                        new_vals["name"] = " ".join(name_build)
                    elif name:
                        split = re.split("[ ]+", name)
                        new_vals["firstname"] = " ".join(split[-1:])
                        new_vals["surname"] = " ".join(split[:-1])

                    # write new partner vals
                    super(res_partner,self).write(cr, uid, [partner_vals["id"]], new_vals, context=context)
                else:
                    # write default
                    super(res_partner,self).write(cr, uid, [partner_vals["id"]], vals, context=context)

            return True

        elif has_name:
            surname, firstname = self._split_name(vals["name"])
            vals["firstname"]=firstname
            vals["surname"]=surname


        ids = util.idList(ids)
        if len(ids) == 1:
            self._check_for_ref(cr,uid,vals,context)

        # default write
        return super(res_partner,self).write(cr, uid, ids, vals, context=context)

    def create(self, cr, uid, vals, context=None):
        self._check_for_ref(cr,uid,vals,context)

        has_name = vals.get("name")
        if not has_name and ("surname" in vals or "firstname" in vals):
            name_build = []
            last_name = vals.get("surname")
            if last_name:
                name_build.append(last_name)
            first_name = vals.get("firstname")
            if first_name:
                name_build.append(first_name)
            name = vals.get("name")
            if name_build:
                vals["name"] = " ".join(name_build)
            elif name:
                split = re.split("[ ]+", name)
                vals["firstname"] = " ".join(split[-1:])
                vals["surname"] = " ".join(split[:-1])

        elif has_name:
            surname, firstname = self._split_name(vals["name"])
            vals["firstname"]=firstname
            vals["surname"]=surname
            

        return super(res_partner,self).create(cr, uid, vals, context=context)

    def _get_mail_salutation(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            salutation = obj.title and obj.title.mail_salutation or None
            name = obj.name
            if salutation:
                salutation = _(salutation)
                if salutation:
                    if "%" in salutation:
                        res[obj.id] = salutation % name
                    else:
                        res[obj.id] = salutation
            else:
                res[obj.id]=name
        return res

    def _get_co_salutation(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            salutation = obj.title and obj.title.co_salutation or None
            name = obj.name
            if salutation:
                salutation = _(salutation)
                if salutation:
                    if "%" in salutation:
                        res[obj.id] = salutation % name
                    else:
                        res[obj.id] = salutation
            else:
                res[obj.id]=name
        return res

    def _build_address_text(self, cr, uid, address, without_company=None, address_type=False, without_name=False, context=None):
        """
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the _country where it belongs.

        :param address: browse record of the res.partner to format
        :param without_company: address with company name
        :param address_type: the address type (supported types: None,mail)
        :returns: the address formatted in a display that fit its _country habits (or the default ones
            if not _country is specified)
        :rtype: string
        """

        _lines = []

        #check default value
        if without_company is None:
            without_company = address.mail_without_company

        _use_parent_address = address.use_parent_address
        _mail_address = _use_parent_address and address.parent_id or address
        _name_address = not without_company and address.parent_id or address

        #check if it is for mail
        if not without_name:
          if address_type == "mail":
              #build name
              title = _name_address.title
              _lines.append(title and "\n".join((title.name,_name_address.name)) or _name_address.name)
              #build co
              if _name_address.id != address.id:
                  co_salutation = address.co_salutation
                  if co_salutation:
                      _lines.append(co_salutation)
          #check with company
          elif _name_address.id != address.id:
              _lines.append(_name_address.name)
          elif _mail_address:
              _lines.append(_mail_address.name)

        _street = _mail_address.street
        _street2 = _mail_address.street2
        _zip = _mail_address.zip
        _city = _mail_address.city
        _state = _mail_address.state_id
        _country = _mail_address.country_id

        if _street:
            _lines.append(_street)

        if _street2:
            _lines.append(_street2)

        _values = []
        if _country and _country.code:
            _values.append(_country.code)
        if _zip:
            _values.append(_zip)
        if _city:
            _values.append(_city)
        if _values:
            _lines.append(" ".join(_values))

        if _country and _country.name:
            _lines.append(_country.name)

        return _lines

    def _display_address(self, cr, uid, address, without_company=None, context=None):
        return "\n".join(self._build_address_text(cr, uid, address, without_company=without_company, context=context))

    def _get_mail_address(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for partner in self.browse(cr, uid, ids, context):
            res[partner.id] = "\n".join(self._build_address_text(cr, uid, partner, address_type="mail", context=context))
        return res
    
    def _get_display_address(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for partner in self.browse(cr, uid, ids, context):
            res[partner.id] = "\n".join(self._build_address_text(cr, uid, partner, context=context))
        return res

    def _get_number(self, cr, uid, ids, num, context=None):
        return re.sub(r"[^0-9+]","", num)

    def _get_phone(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for partner in self.browse(cr, uid, ids, context):
            if partner.phone:
                res[partner.id] = self._get_number(cr, uid, ids, partner.phone)
        return res

    def _get_mobile(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for partner in self.browse(cr, uid, ids, context):
            if partner.mobile:
                res[partner.id] = self._get_number(cr, uid, ids, partner.mobile)
        return res

    def _get_fax(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for partner in self.browse(cr, uid, ids, context):
            if partner.fax:
                res[partner.id] = self._get_number(cr, uid, ids, partner.fax)
        return res

    def _split_name(self, name):
        split = re.split("[ ]+", name)
        firstname = " ".join(split[-1:])
        surname   = " ".join(split[:-1])
        return (surname, firstname)

    def _get_login_id(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        cr.execute("SELECT p.id, u.id FROM res_users u "
                   " INNER JOIN res_partner p ON p.id = u.partner_id "
                   " WHERE p.id IN %s", (tuple(ids),))

        for (partner_id, login_id) in cr.fetchall():
            res[partner_id]=login_id
        return res
    
    def _get_contact_info(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids)
        for obj in self.browse(cr, uid, ids, context):
            info = [obj.name]
            if obj.phone:
                info.append(obj.phone)
            if obj.mobile:
                info.append(obj.mobile)
            if obj.email:
                info.append(obj.email)
            res[obj.id] = "\n".join(info)
        return res
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        res = super(res_partner,self).name_search(cr, uid, name, args=args, operator=operator, context=context, limit=limit)
        if not res:
            ids = self.search(cr, uid, [("ref",operator,name)], limit=limit, context=context)
            if ids:
                return self.name_get(cr, uid, ids, context=context)                
        return res

    _inherit = "res.partner"
    _columns =  {
        "mail_without_company" : fields.boolean("Mail Address without company"),
        "mail_salutation" : fields.function(_get_mail_salutation, type="text",string="Mail Salutation"),
        "mail_address" : fields.function(_get_mail_address,type="text",string="Mail Address"),
        "display_address" : fields.function(_get_display_address,type="text",string="Address"),
        "contact_info" : fields.function(_get_contact_info,type="text",string="Contact Info"),
        "co_salutation" : fields.function(_get_co_salutation, type="text", string="C/O Salutation"),
        "phone_n" : fields.function(_get_phone, type="char", store=True, string="Phone normalized"),
        "mobile_n" : fields.function(_get_mobile, type="char", store=True, string="Mobile normalized"),
        "fax_n" : fields.function(_get_fax, type="char", store=True, string="Fax normalized"),
        "birthday" : fields.date("Birthday"),
        "firstname" : fields.char("First Name"),
        "surname" : fields.char("Last Name"),
        "login_id" : fields.function(_get_login_id, string="Login", type="many2one", obj="res.users", copy=False, readonly=True)
     }
