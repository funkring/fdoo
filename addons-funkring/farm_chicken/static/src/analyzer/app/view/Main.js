var filterList = Ext.create('Ext.List', {
   flex : 1,
   store: {
     fields: ['name'],
     data: [{"name":"Test1"}]
   },
   itemTpl: '{name}'
});

var optionPanel = Ext.create('Ext.Panel', {
   flex : 1,
   layout : {
       type : 'vbox'
   },
   items : [
        {
            xtype : 'toolbar',
            docked : 'top',
            items : [
                {
                    xtype : 'button',
                    text
                    
                }
            ]   
        }
   ]
});

var navPanel = Ext.create('Ext.Panel', {    
    flex : 1,
    layout: {
        type : 'vbox'
    },
    items : [
        {
            xtype: 'toolbar',
            docked: 'top',
            items : [
                {
                    xtype: 'button',
                    text: 'Hinzufügen',
                    handler: function() {
                        /*
                        view.push({
                                         
                             xtype: 'panel',
                             flex: 1,
                             items : [
                                xtype: 'toolbar',
                                docked: 'top'
                             ]                                          
                        });*/
                    }
                }
            ]
            
        },       
        filterList
    ]
});

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
            navPanel,
            {
                xtype: 'panel',
                html: 'Chart',
                flex: 2
            }         
        ]
    }
});
