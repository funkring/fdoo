# -*- encoding: utf-8 -*-

#########################################################################
#                                                                       #
# Copyright (C) 2009  Domsense s.r.l.                                   #
# @authors: Simone Orsi													#				       
# Copyright (C) 2009-2011  Alistek, Ltd                                 #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

{
    'name': 'Aeroo Reports',
    'version': '2.0',
    'category': 'Generic Modules/Aeroo Reporting',
    'description': """Gives possibility to easily create complicated reports.
                    Requires "aeroolib" to be installed.
                    """,
    'author': 'Alistek Ltd featured by Martin Reisenhofer',
    'website': 'http://www.alistek.com',
    'depends': ['base','report'],    
    'data': ["security.xml",
             "data/report_aeroo_data.xml",
             "report_view.xml", 
             "report_html.xml",
            ],
    'installable': True,
    'auto_install': False,
}
