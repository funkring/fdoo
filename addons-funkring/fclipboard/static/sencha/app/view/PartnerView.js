/*global Ext:false*/

Ext.define('Fclipboard.view.PartnerView', {
    extend: 'Fclipboard.view.FormView',    
    xtype: 'partnerform',
    config: {
        items: [
            {
                xtype: 'fieldset',
                title: 'Kontakt',
                items: [
                    {
                        xtype: 'textfield',
                        name: 'name',
                        label: 'Name',
                        required: true
                    },
                    {
                        xtype: 'textfield',
                        name: 'email',
                        label: 'E-Mail'
                    },
                    {
                        xtype: 'textfield',
                        name: 'mobile',
                        label: 'Mobil'
                    },
                    {
                        xtype: 'textfield',
                        name: 'phone',
                        label: 'Telefon'
                    },
                    {
                        xtype: 'textfield',
                        name: 'fax',
                        label: 'Fax'
                    }
                ]   
            },
            {
               xtype: 'fieldset',
               title: 'Adresse',
               items: [
                    {
                        xtype: 'textfield',
                        name: 'street',
                        label: 'Straße'                    
                    },
                    {
                        xtype: 'textfield',
                        name: 'street2',
                        label: 'Straße2'
                    },                
                    {
                        xtype: 'textfield',
                        name: 'zip',
                        label: 'PLZ'
                    },
                    {
                        xtype: 'textfield',
                        name: 'city',
                        label: 'Ort'
                    }
               ] 
            }            
        ]       
    }
    
});