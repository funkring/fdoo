/*global Ext:false*/
Ext.define('Fclipboard.model.Item', {
   extend: 'Ext.data.Model',
   requires: [
       'Fclipboard.proxy.PouchDB'
   ],
   config: {
       fields: ['_id', 'name', 'partner_id', 'parent_id', 'form', 'type'],
       belongsTo: 'parent_id',
       proxy: {
            type: 'pouchdb',
            database: 'fclipboard',
            domain: [['fdoo__ir_model','=','fclipboard.item']]      
       }       
   }
});