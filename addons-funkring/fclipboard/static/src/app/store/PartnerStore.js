/*global Ext:false*/

Ext.define('Fclipboard.store.PartnerStore', {
    extend: 'Ext.data.Store',
    config: {
        proxy: {
            type: 'pouchdb',
            database: 'fclipboard',
            domain: [['fdoo__ir_model','=','res.partner']]      
        }
    }
});
