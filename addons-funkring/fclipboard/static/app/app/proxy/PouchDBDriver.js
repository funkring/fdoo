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
    
    resetDB: function(dbName, callback) {
        var self = this;
        var db = self.getDB(dbName);
        db.destroy(callback);
        self.databases[dbName] = undefined;
    },

     /**
     * sync odoo store
     */
    syncOdooStore: function(con, db, store, syncUuid, res_model, log, callback) {        
        var syncpointUuid = "_local/"+syncUuid+"{"+res_model+"}";
        var jdoc_obj = con.get_model("jdoc.jdoc");
        
        // delete docs
        
        // download docs
        
        // load changes
        
        // publish change
        
        // fetch changes
        var syncChanges = function(syncPoint) {
            db.changes({
                include_docs: true,
                since: syncPoint.seq,
                filter: function(doc) {
                    return doc.fdoo__ir_model === res_model;
                }
            }).then(function(changes) {
                jdoc_obj.exec("jdoc_sync", 
                     [
                       {
                        "model" : res_model,
                        "lastsync" : syncPoint,
                        "changes" : changes.results || {}
                       },
                       con.user_context
                     ],                       
                     null, 
                     function(err, res) {
                         if ( err ) {                                                             
                             log.error(err);
                         } else {
                             var server_changes = res.changes;
                             var server_lastsync = res.lastsync;
                             var pending_server_changes = server_changes.length+1;
                             
                                                          
                             var serverChangeDone = function(err) {
                                pending_server_changes--;
                                
                                if ( err ) {
                                    log.warning(err);
                                }
                                
                                if ( !pending_server_changes ) {
                                    log.info("Synchronisation abgeschlossen!");        
                                   
                                    db.info().then(function(res) {
                                        server_lastsync.seq = res.update_seq;
                                        server_lastsync._id = syncPoint._id;
                                        
                                        db.get(server_lastsync._id, function(err, doc) {
                                           if (err) {
                                               db.put(server_lastsync, function(err) {
                                                   log.info("Synchronisationspunkt erstmals erstellt!");
                                                   callback(err,server_lastsync);
                                               });
                                           } else {
                                              server_lastsync._rev = doc._rev;
                                              db.put(server_lastsync, function(err) {
                                                   log.info("Synchronisationspunkt erstellt!");
                                                   callback(err,server_lastsync);
                                               });
                                           }
                                        });
                                    });           
                                }                              
                                 
                             };
                             
                             // iterate changes
                             Ext.each(server_changes, function(server_change) {
                                // handle delete
                                if ( server_change.deleted ) {
                                    
                                    // lösche dokument
                                    db.get(server_change.id, function(err, doc) {
                                         if ( !err ) {
                                            doc._deleted=true;                                          
                                            log.info("Dokument " + server_change.id + " wird gelöscht");
                                            db.put(doc, serverChangeDone); //<- decrement pending operations
                                         } else {
                                            log.warning("Dokument " + server_change.id + " nicht vorhanden zu löschen");
                                            // decrement operations
                                            serverChangeDone(); 
                                         }                                      
                                    });
                                    
                                //handle update
                                } else if ( server_change.doc ) {
                                    db.get(server_change.id, function(err, doc) {
                                         if ( err ) {
                                             log.warning("Dokument " + server_change.id + " wird neu erzeugt");
                                         } else {                                         
                                             server_change.doc._rev = doc._rev;
                                             log.info("Dokument " + server_change.id + " wird aktualisiert");
                                         }
                                         db.put(server_change.doc, serverChangeDone); //<- decrement pending operations                                         
                                    });
                                }
                             });
                             
                             // changes done
                             serverChangeDone();
                         }
                     });                                
            }).catch(function(err) {
                log.error(err);
            });
        };
        
        
        // get last syncpoint or create new
        db.get(syncpointUuid).then( function(doc) {
            syncChanges(doc);                             
        }).catch( function(err) {
            syncChanges({
                "_id" : syncpointUuid,
                "date" : null,
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
                var res_model =  defaults.fdoo__ir_model;
                if ( res_model) {
                    // get database                    
                    var db = self.getDB(proxy.getDatabase());
                    self.syncOdooStore(con, db, store, syncuuid, res_model, log, callback);
                }
            }
         };
        
                     
         // start sync                    
         con.authenticate( function(err)  {
             if (err) {
                 log.error(err);
             } else {
                 log.info("Authentifizierung erfolgreich");                     
                 Ext.each(stores, syncStore);                                 
             }
         } );
        
    }
    
});