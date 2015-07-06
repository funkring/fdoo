/*global Ext:false*/

Ext.define('Fclipboard.store.PartnerStore', {
    extend: 'Ext.data.Store',      
    config: {
        model: 'Fclipboard.model.Partner',
        sorters: 'name',
        grouper: function(record) {
            return record.get('name')[0];
        }
    }
});
