/*global Ext:false*/
Ext.define('Fclipboard.model.Partner', {
   extend: 'Ext.data.Model',
   requires: [
       'Fclipboard.proxy.PouchDB'
   ],
   config: {
       fields: ['name', 'street', 'mobile', 'phone', 'zip'],
       identifier: 'uuid',
       proxy: {
            model: 'Fclipboard.model.Partner',
            type: 'pouchdb',
            database: 'fclipboard',
            domain: [['fdoo__ir_model','=','res.partner']]      
        }
   } 
});