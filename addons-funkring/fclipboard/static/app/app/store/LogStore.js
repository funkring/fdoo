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
        var self = this;
        this.add({"message": self.extract(message),
                  "prio" : 1});
    },
    
    error: function(message) {
        var self = this;
        this.add({"message": self.extract(message),
                  "prio" : 2});
    },
    
    warning: function(message) {
        var self = this;
        this.add({"message": self.extract(message),
                  "prio" : 3});
    },    
    
    extract: function(message) {   
        if ( typeof message == "object") {
            var res = "";
            if ( message.message ) {
               res = message.message + "\n";
            }            
            if (message.data && message.data.message) {
               res = res + message.data.message;
            }
            return res; 
        } else {
            return message;
        }
    }
    
});
