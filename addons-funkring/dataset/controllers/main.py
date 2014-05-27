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

from openerp.addons.web import http
from openerp.addons.web.http import request
import simplejson
import logging
import openerp

_logger = logging.getLogger(__file__)

STATE_INVALID = 0
STATE_PREPARED = 1
STATE_VALID = 2

class ChangeIterator():

    def __init__(self, pool, uid, models, params, timeout, receiver):
        # initialize
        self.uid = uid
        self.cr = pool.db.cursor()
        self.timeout = timeout
        self.pool = pool
        self.models = models
        self.params = params
        self.receiver = receiver
        self.events = {}
        
        # set auto commit
        self.cr.autocommit(True)
        self.state = STATE_PREPARED
        
    def close(self):
        if self.state:
            self.state = STATE_INVALID
            try:
                self.cr.close()
            finally:
                self.cr = None
                self.pool = None
                
    def __del__(self):
        self.close()
            
    def __iter__(self):
        return self
    
    def _get_changesets(self,events):
        res = []
        view_obj = self.pool.get("dataset.view")
        for model in self.models:
            model_obj = self.pool.get(model)
         
            if model_obj and model_obj._event in events:
                # ignore events from it own
                event_param = events.get(model_obj._event)
                if isinstance(event_param,dict):
                    sender = event_param.get("sender")
                    if sender and sender == self.receiver:
                        continue
                
                # get model params
                model_param = self.params and self.params.get(model) or None
                model_schema = None
                model_domain = None
                # check if schema and domain is defined 
                if model_param:
                    model_schema = model_param.get("schema")
                    model_domain = model_param.get("domain")
            
                # build changeset
                changeset = view_obj.data_changeset(self.cr,self.uid,
                                                    model_obj._name,
                                                    schema=model_schema,
                                                    domain=model_domain)
                res.append(changeset)
        return res
    
    def __next__(self):
        return self.next()
        
    def next(self):
        if not self.state:
            raise StopIteration
        
        res = None
        events = {}
        
        # enable notify (Think about that model could be reloaded)
        for model in self.models:
            model_obj = self.pool.get(model)
            if model_obj and (not model_obj._chgnotify_enabled or self.state==STATE_PREPARED):
                model_obj._chgnotify_enabled = True
                self.cr.event_listen(model_obj._event)
                events[model_obj._event]=None
                
        if self.state==STATE_PREPARED:
            self.state=STATE_VALID
  
        # check for new enabled
        if events:
            res = self._get_changesets(events)
        # if no res before wait for event
        else:
            events = self.cr.event_wait(self.timeout)
            if events:
                res = self._get_changesets(events)
        
        #finish - no event
        res = "%s\n" % ((res and simplejson.dumps(res) or ""),)
        return res
        

class DataSet(http.Controller):

    @http.route('/web/dataset/_changes', type='http', auth="user")
    def changes(self, models=None, model=None, params=None, timeout=30, receiver=None):
        """
        @param models  [{ model : "model.name", domain : []}]
        """
        # only one model        
        if model:            
            models = [model]
        # models
        elif models and isinstance(models,basestring):
            models = simplejson.loads(models)
        # params
        if params and isinstance(params,basestring):
            params = simplejson.loads(params)

        if isinstance(timeout,basestring):
            timeout = int(timeout)

        pool = request.registry       
                
        if models: 
            chg_gen = ChangeIterator(pool, request.uid, models, params, timeout, receiver)
            resp = request.make_response(chg_gen,
                            headers=[("Cache-Control","no-cache"),
                                    ("Content-Type","text/plain")]             
                    )
            
            resp.call_on_close(chg_gen.close)
            return resp
        else:
            raise Exception("No model found for listening!")
