/*global Ext:false*/

Ext.define('Fclipboard.store.ItemStore', {
    extend: 'Ext.data.Store',    
    config: {
        domain: null,
        model: 'Fclipboard.model.Item'       
    }
});
