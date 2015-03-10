/*global Ext:false,PouchDB:false,FdbUtil:false*/

Ext.define('Fclipboard.proxy.PouchDBDriver',{
    alternateClassName: 'PouchDBDriver',
    singleton: true,
    databases: {},
    getDB: function(dbName) {        
        var self = this;
        if ( dbName in self.databases ) {
            return self.databases[dbName];
        } else {
            var db = new PouchDB(dbName);
            self.databases[dbName] = db;
            return db;
        } 
    },
    
    buildDomainQuery: function(domain, values, nobuild) {
      if (!domain) {
          return null;
      }
      
      var i, value, field, stmt, op;
      var ifstmt='';
      var ifstmt_op='&&';      
      var defaults={};
      
      for (i=0; i<domain.length;i++) {
          var tupl = domain[i];
          stmt = null;
          if ( tupl.constructor === Array && tupl.length == 3) {
              field = tupl[0];
              op = tupl[1];
              value = tupl[2];
              
              if ( op === '=') {
                  if (typeof value === 'string' ) {
                    op = '===';
                  }   
                      
                  if (values) {
                    values[field]=value;
                  }                       
              }    
              
              if ( value === undefined || value === null) {
                  value = "null";
              } else {
                  value = value.toString();
              }
                            
              stmt = 'doc.' + field + ' ' + op + ' ' + value; 
          } 
          
          if ( stmt !== null) {
              if ( ifstmt.length > 0 ) {
                  ifstmt += ' ';
                  ifstmt += ifstmt_op;  
                  ifstmt += ' ';
              }
              ifstmt += '(';
              ifstmt += stmt;
              ifstmt += ')';
          }          
      }
      
      if ( ifstmt.length === 0 || nobuild) { 
          return null;
      }
      
      return new Function('doc', 'if ( ' + ifstmt + ' ) emit(doc);');       
    },
     
    joinDomain: function(result, domain) {
        if (domain) {
            if (!result) {
                result = domain;
            } else {
                result = result.concat(domain);
            }
        }
        return result;
    }
});