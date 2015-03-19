/*global Ext:false*/
Ext.define('Fclipboard.model.Item', {
   extend: 'Ext.data.Model',
   requires: [
       'Fclipboard.proxy.PouchDB'
   ],
   config: {
       fields: ['name', 'partner_id', 'parent_id', 'form', 'type'],
       belongsTo: 'parent_id',
       identifier: 'uuid',
       proxy: {
            type: 'pouchdb',
            database: 'fclipboard',
            domain: [['fdoo__ir_model','=','fclipboard.item']]      
       }       
   }
});