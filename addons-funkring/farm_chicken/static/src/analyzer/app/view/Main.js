Ext.define('ChickenFarmAnalyzer.view.Main', {
    extend: 'Ext.Container',
    xtype: 'main',
    requires: [
    ],
    config: {
        fullscreen: true,
        layout: {
            type: 'hbox'
        },        
        items: [            
            {
                xtype: 'panel',                
                flex: 1,                
                items : [
                    {
                        xtype: 'toolbar',
                        docked: 'top',
                        items: [
                            {
                                xtype: 'button',
                                text: "Add"
                            }
                        ]       
                    }
                ]
            },
            {
                xtype: 'panel',
                html: 'Chart',
                flex: 2
            }         
        ]
    }
});
