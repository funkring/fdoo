/*global Ext:false*/

Ext.define('Fclipboard.view.ItemList',{
    extend: 'Ext.List',
    xtype: 'item_list',
    config: {
        store: 'Items',
        itemTpl: '<div>{name}</div>'
    }    
});

