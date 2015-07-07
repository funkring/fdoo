/*global Ext:false*/

Ext.define('Fclipboard.view.ConfigView', {
    extend: 'Fclipboard.view.FormView',    
    xtype: 'configform',
    config: {
        items: [
            {
                xtype: 'fieldset',
                title: 'Kontakt',
                items: [
                    {
                        xtype: 'hiddenfield',
                        name: '_rev',
                        label: 'Version'
                    },
                    {
                        xtype: 'textfield',
                        name: 'host',
                        label: 'Server',
                        required: true
                    },
                    {
                        xtype: 'textfield',
                        name: 'port',
                        label: 'Port',
                        required: true
                    },
                    {
                        xtype: 'textfield',
                        name: 'db',
                        label: 'Datenbank',
                        required: true
                    },
                    {
                        xtype: 'textfield',
                        name: 'user',
                        label: 'Benutzer',
                        required: true
                    },
                    {
                        xtype: 'passwordfield',
                        name: 'password',
                        label: 'Passwort',
                        required: true
                    }
                ]   
            },
            {
                xtype: 'fieldset',
                title: 'Zurücksetzen',
                items: [
                    {
                        xtype: 'button',
                        text: 'Sync-Daten löschen',
                        ui: 'default',
                        action: 'resetSync'
                    }            
                ]
            }        
        ]       
    }
    
});