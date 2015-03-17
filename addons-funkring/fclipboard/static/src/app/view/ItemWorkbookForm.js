/*global Ext:false*/

Ext.define('Fclipboard.view.ItemWorkbookForm', {
    extend: 'Fclipboard.view.FormView',
    xtype: 'item_workbook',
    
    requires: [
        'Fclipboard.view.FormView'
    ],
    
    config: {
        title: 'Arbeitsmappe',
        items: [
            {
                xtype: 'textfield',
                name: 'name',
                label: 'Name',
                required: true
            },
            {
                xtype: 'selectfield',
                name: 'partner_id',
                label: 'Partner',
                store: 'PartnerStore',
                valueField: '_id',
                displayField: 'name'
            }
        ]
    },
    
   
});