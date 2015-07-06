/*global Ext:false,PouchDB:false*,openerplib:false, console:false*/

Ext.define('Ext.proxy.PouchDBDriver',{
    alternateClassName: 'PouchDBDriver',
    
    singleton: true,
    
    config: {        
    },
                
    constructor: function(config) {
        this.callParent(arguments);
        this.databases = {};
    },
        
    /**
     * @return database
     */
    getDB: function(dbName) {    
        var db = this.databases[dbName];
        if ( db === undefined ) {
            db =  new PouchDB(dbName);
            this.databases[dbName] = db;
        }
        return db;
    },    
    
    

    /**
     * sync odoo store
     */
    syncOdooStore: function(db, store, syncUuid, res_model, log, callback) {        
        var syncPoint;
        var syncpointUuid = "_local/"+syncUuid+"{"+res_model+"}";
        
        // delete docs
        
        // download docs
        
        // load changes
        
        // publish change
        
        // fetch changes
        var fetchChanges = function(syncPoint) {
            
        };
        
        
        // get last syncpoint or create new
        db.get(syncpointUuid).then( function(doc) {
            fetchChanges(doc);                             
        }).catch( function(err) {
            fetchChanges({
                "_id" : syncpointUuid,
                "date" : null,
                "id" : null,
                "sequence" : 0
            });
        });
                    
      
    },
    
    /**
     * sync with odoo
     */
    syncOdoo: function(credentials, stores, log, callback) {
         var self = this;
         var con = openerplib.get_connection(credentials.host, 
                                            "jsonrpc", 
                                            parseInt(credentials.port,10), 
                                            credentials.db, 
                                            credentials.user, 
                                            credentials.password);
                           
         var syncuuid = "odoo_sync_{"+credentials.user + "}-{" + credentials.host + "}-{" + credentials.port.toString() + "}-{" + credentials.user +"}";
         var jdoc_obj = con.get_model("jdoc.jdoc");
         var mapping_obj = con.get_model("res.mapping");
         var res_model = null;
         var localChanges = {};
         
         if ( !log ) {
             log = function() {
                 this.log = function(message) {
                     console.log(message);
                 };
                 this.error = this.log;
                 this.warning = this.log;
                 this.debug = this.log;
                 this.info = this.log;
             };
         }
       
         // prepare store sync
         var syncStore = function(store) {
            var proxy = store.getProxy();
            if ( proxy instanceof Ext.proxy.PouchDB ) {
                var defaults = proxy.getDefaults();
                res_model =  defaults.fdoo__ir_model;
                if ( res_model) {
                    // get database                    
                    var db = self.getDB(proxy.getDatabase());
                    self.syncOdooStore(db, store, syncuuid, res_model, log, callback);
                }
            }
         };
        
                     
         // start sync                    
         con.authenticate( function(res, err)  {
             if (err) {
                 log.error(err);
             } else {
                 log.info("Authentifizierung erfolgreich");                     
                 Ext.each(stores, syncStore);                                 
             }
         } );
        
    }
    
});