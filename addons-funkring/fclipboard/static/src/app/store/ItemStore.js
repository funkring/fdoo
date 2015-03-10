/*global Ext:false*/

/*
Ext.define('Fclipboard.store.Items', {
    extend: 'Ext.data.Store',
    config: {
        model: 'Fclipboard.model.Item',
        data: [{"id":1,"name":"Product 1","type":"product_amount","sequence":1},
               {"id":2,"name":"Product 2","type":"product_amount","sequence":2}]
    }
});*/


Ext.define('Fclipboard.store.ItemStore', {
    extend: 'Ext.data.Store',
    config: {
        proxy: {
            type: 'pouchdb',
            database: 'fclipboard',
            domain: [['fdoo__ir_model','=','fclipboard.item']]      
        }
    }
});
