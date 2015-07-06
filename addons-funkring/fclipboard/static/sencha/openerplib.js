
/**
 * The Odoo LIB
 */
var openerplib = {
    
};

openerplib.json_rpc = function(url, fct, params, callback) {
    var data = {
        jsonrpc : "2.0",
        params: params,
        id: Math.floor((Math.random() * 1000000000) + 1)
    };
    
    //check function
    if (fct) {
        data.method = fct;
    }
    
    var req = new XMLHttpRequest();
    req.open("POST", url, true /*async*/);
    //req.withCredentials = true;
    req.setRequestHeader("Content-Type", "application/json");
    req.onreadystatechange = function () {
        if (req.readyState !== 4 || !callback) {
            return;
        }

        var contentType = req.getResponseHeader('Content-Type');
        if (req.status !== 200) {
            callback(null,'Expected HTTP response "200 OK", found "' + req.status + ' ' + req.statusText + '"');
        } else if (contentType.indexOf('application/json') !== 0) {
            callback(null, 'Expected JSON encoded response, found "' + contentType + '"');
        } else {
            var result = JSON.parse(this.responseText);
            callback(result.result || null, result.error || null);
        }
    };

    // send request
    req.send(JSON.stringify(data));
};

/**
 * JsonRPC Connector
 */ 
openerplib.JsonRPCConnector = function(url, database, login, password, user_id) {
    this._url = url;
    this._url_jsonrpc = url + "/jsonrpc";
    this._password = password;   
    this.login = login;
    this.database = database;
    this.user_id = user_id;
    this.session_id = null;
    this.user_context = null;
    
    var self = this;
        
    this.authenticate = function(callback) {
        var params = {
            "db" : self.database,
            "login": self.login,
            "password" : self._password 
        };
        
        var url = self._url + "/web/session/authenticate";
        openerplib.json_rpc(url, null, params, function(res,err) {
            
            if ( err === null ) {
                // update session data
                self.session_id = res.session_id;
                self.user_id = res.user_id;
                self.user_context = res.user_context;
            }
            
            // callback
            if ( callback ) {
                callback(res, err);
            }
        });        
    };
    
    this.send = function(service_name, method, args, callback) {
        openerplib.json_rpc(self._url, "call", { service: service_name, method: method, args: args }, callback);
    };
    
    this.get_service = function(service_name) {
        return function() {
            this.call = function(method, args, callback) {
                self.send(service_name, method, args, callback);
            };
        };
    };
    
    this.get_model = function(model_name) {
        var service = self.get_service("object");
        return function() {
            this.call = function(method, args, kwargs, callback) {
                service.call("execute_kw",
                             [ self.database, 
                               self.user_id, 
                               self._password,
                               model_name,
                               method,
                               args, 
                               kwargs ],
                             callback);   
            };
        };
    };
    
};

    
/**
 * Simple OpenERP Client
 */
openerplib.get_connection = function(host, protocol, port, database, login, password) {
    if ( !port ) {
        port = 8069;
    }    
    
    var url = host + ":" + port.toString();
    switch ( protocol ) {
        case "jsonrpcs":
            url = "https://" + url;
            break;
        default:
            url = "http://" + url;
            break;
    }
      
    return new openerplib.JsonRPCConnector(url, database, login, password, null);
};




