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
{
    "name" : "oerp.at Austria 2010 - Chart of Accounts",
    "description":"""        
        oerp.at Extended Chart of Accounts 
    """,
    "version" : "1.0",
    "author" :  "funkring.net",
    "website": "http://www.funkring.net",
    "category" : "Localization/Account Charts",
    "depends" : ["account_chart",
                 "base_vat"],    
    "data" : ["data/account_tax_code_base.xml",
                    "data/account_tax_code.xml",
                    "data/account_chart_base.xml",
                    "data/account_chart.xml",
                    "data/account_template.xml",
                    "data/account_tax.xml",
                    "data/account_fpos.xml",
                    "view/austrian_erp_wizard.xml"],
    "auto_install" : False,
    "installable": True
}