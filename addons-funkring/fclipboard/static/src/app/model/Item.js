/*global Ext:false*/

Ext.define('Fclipboard.model.Item',{    
    extend: 'Ext.data.Model',
    requires: ['Ext.data.proxy.Sql'],
    config: {
        idProperty: 'id',
        fields: [
            {name:'id', type:'int'},
            {name:'name', type:'string'},
            {name:'parent_id', type:'int'},
            {name:'type', type:'string'},
            {name:'sequence', type:'int'}
        ],
        validations: [
            {type: 'presence', field:'id'},
            {type: 'presence', field:'name'},
            {type: 'presence', field:'type'}
        ]
    },
    proxy: {
        type: "sql",
        database: "fclipboard",
        table: "fclipboard_item"
    }
});