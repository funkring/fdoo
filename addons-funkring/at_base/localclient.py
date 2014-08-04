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

from openerp.service import model 

class LocalConnection(object):
    """
    A class to represent a connection with authentication to an OpenERP Server.
    It also provides utility methods to interact with the server more easily.
    """
    def __init__(self, cr, uid, context):
        self.cr = cr
        self.uid = uid
        self.context = context
        
    def get_model(self, model_name):
        """
        Returns a Model instance to allow easy manipulation of an OpenERP model.

        :param model_name: The name of the model.
        """
        return Model(self, model_name)
    
class Model(object):
    """
    Useful class to dialog with one of the models provided by an OpenERP server.
    An instance of this class depends on a Connection instance with valid authentication information.
    """

    def __init__(self, connection, model_name):
        """
        :param connection: A valid Connection instance with correct authentication information.
        :param model_name: The name of the model.
        """
        self.connection = connection
        self.model_name = model_name

    def __getattr__(self, method):
        """
        Provides proxy methods that will forward calls to the model on the remote OpenERP server.

        :param method: The method for the linked model (search, read, write, unlink, create, ...)
        """
        def proxy(*args, **kw):
            """
            :param args: A list of values for the method
            """
            #execute_cr(cr, uid, obj, method, *args, **kw):
            result =  model.execute_cr(self.connection.cr, self.connection.uid, self.model_name, method, *args, **kw)
            return result
            
        return proxy