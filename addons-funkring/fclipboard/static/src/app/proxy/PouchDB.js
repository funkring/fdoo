/*global Ext:false,PouchDB:false,PouchDBDriver:false*/

Ext.define('Fclipboard.proxy.PouchDB', {
    extend: 'Ext.data.proxy.Proxy',
    alias: 'proxy.pouchdb',
    requires: [
        'Fclipboard.proxy.PouchDBDriver'
    ],
    config: {
        /**
         * @cfg {Object} reader
         * @hide
         */
        reader: null,
        /**
         * @cfg {Object} writer
         * @hide
         */
        writer: null,       
        /**
         * @cfg {String} database
         * Database name to access tables from
         */
        database: null, 
        /**
         * @cfg {List} domain 
         * Tuple list of filters
         */
        domain: null
    },
    
     /**
     * Creates the proxy, throws an error if local storage is not supported in the current browser.
     * @param {Object} config (optional) Config object.
     */
    constructor: function(config) {
        this.callParent(arguments);
        this.domain = config.domain;
        if (typeof config.database == 'string') {
            this.db = new PouchDB(config.database);
        } else {
            this.db = PouchDBDriver.getDB(config.database);
        }
        
    },
    
    // setException helper
    setException: function(operation, err) {
        if (err) {
            this.fireEvent('exception', this, operation);
            operation.setException(err);
        }
    },
    
    // callback helper
    tryCallback: function(result, callback, scope, err) {
        if (typeof callback == 'function') {
            if ( err ) {
                callback.call(scope || this, result, err);
            } else {
                callback.call(scope || this, result);
            }
        }
    },
             
    // read function
    read: function(operation, callback, scope) {
        var self = this;
        var params = {'include_docs':true};
        var filter_domain = self.domain;
        var sorters = operation.getSorters();
        var filters = operation.getFilters();
        
        var operation_params = operation.getParams();
        if (operation_params) {
            Ext.apply(params, operation_params);
            filter_domain = PouchDBDriver.joinDomain(filter_domain, operation_params.domain);                         
        } 
        
        operation.setStarted();
        
        //result function
        var res = function(err, response){            
            var result; 
            var records = [];
          
            if (err) {
                result = Ext.data.ResultSet({
                            records: records,
                            success: false,
                            total: 0,
                            count: 0
                        });                        
                self.setException(operation, err);
                        
            } else {
            
                var i, data, ln;
                    
                for ( i = 0; i<response.rows.length; i++) {
                    data = response.rows[i].doc;
                    records.push({
                       id: response._id, 
                       data: data,
                       node: data
                    });
                }                
                
                //build result set
                result = Ext.data.ResultSet({
                    records: records,
                    success: true,
                    total: response.total_rows,
                    count: response.rows.length
                });
                      
                      
                // handle filter and sorters
                var hasFilters = filters && filters.length;
                var hasSorters = sorters && sorters.length;
                //                        
                if (hasFilters || hasSorters) {
                    var filtered = Ext.create('Ext.util.Collection', function(record) {
                        return record.getId();
                    });
                    
                    // add filters
                    if ( hasFilters ) {
                        filtered.setFilterRoot('data');
                        filtered.addFilters(filters);
                    }
                    
                    // add sorters
                    if ( hasSorters ) {
                        filtered.addSorters(sorters);                          
                    }
                    
                    //filter and sort
                    filtered.addAll(result.getRecords());
                    operation.setRecords(filtered.items.slice());
                    
                    //update result
                    result.setRecords(operation.getRecords());
                    result.setCount(filtered.items.length);
                    result.setTotal(filtered.items.length);
                }                 
            }            
            
            self.tryCallback(result, callback, scope, err);
        };                
        
        //query all or filter
        var build_query = PouchDBDriver.buildDomainQuery(filter_domain);
        if (build_query !== null) {
            self.db.query(build_query,params,res);       
        } else {
            self.db.allDocs(params,res);
        } 
        
    },
    
    // update function
    update: function(operation, callback, scope) {
        var self = this;        
        operation.setStarted();
                        
        Ext.each(operation.records, function(record) {           
           self.db.put(record.data, function(err,response) {
                if (err) {
                    // handle error
                    self.setException(operation, err);
                    self.tryCallback(operation, callback, scope);
                } else {
                    //fetch data again
                    self.db.get(response.id, {"rev":response.rev}, function(err,response){
                        //set data from response
                        self.setException(operation, err);
                        record.data = response;
                        self.tryCallback(operation, callback, scope);
                    });
                }               
           });
        });
    },
    
    // create function is the same as update
    create: function(operation, callback, scope) {
        return this.update(operation, callback, scope);
    },
    
    // destroy
    destroy: function(operation, callback, scope) {
        var self = this;        
        operation.setStarted();
        
        Ext.each(operation.records, function(record) {           
           self.db.remove(record.data, function(err,response) {
                if (err) {
                    self.setException(operation, err);
                    self.tryCallback(operation, callback, scope);
                } else {
                    self.tryCallback(operation, callback, scope);                    
                }               
           });
        });        
    }
    
});