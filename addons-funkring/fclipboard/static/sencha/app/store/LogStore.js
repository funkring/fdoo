/*global Ext:false*/

Ext.define('Fclipboard.store.LogStore', {
    extend: 'Ext.data.Store',    
    config: {
        fields: [
            { name: "message", type:"string" },
            { name: "prio", type:"int" }
        ],
        data: []       
    },
    
    info: function(message) {
        this.add({"message":message,
                  "prio" : 1});
    },
    
    error: function(message) {
        this.add({"message":message,
                  "prio" : 2});
    },
    
    warning: function(message) {
        this.add({"message":message,
                  "prio" : 3});
    }
    
    
});
