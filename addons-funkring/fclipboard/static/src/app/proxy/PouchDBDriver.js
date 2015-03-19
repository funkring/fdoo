/*global Ext:false,PouchDB:false,FdbUtil:false*/

Ext.define('Fclipboard.proxy.PouchDBDriver',{
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
    }    
    
});