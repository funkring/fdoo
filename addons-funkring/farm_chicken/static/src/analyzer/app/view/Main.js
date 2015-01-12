/*global Ext:false,alert:false*/

var formPanel = Ext.create('widget.formpanel',{
   items: [{
       xtype: 'fieldset',
       title: 'Produktion',       
       items: [
       {             
             xtype: 'selectfield',
             label: 'Produktion 1',
             valueField: 'name',
             displayField: 'name',
             store: {
                 fields: ['name'],
                 data: [
                    { name: 'Item 1'},
                    { name: 'Item 2'},
                    { name: 'Item 3'}
                 ]
            }
       }]
   }]    
});

var navPanel = Ext.create('widget.navigationview',{
    flex : 1,
    items: [
        formPanel
    ]    
});


var graphPanel = Ext.create('widget.panel', {
   flex : 2,
   layout: {
      type: 'vbox'
   }, 
   items : [
        {
            xtype: 'toolbar',
            docked: 'top',
            items: [
            
            ]        
        }
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
            graphPanel  
        ]
    }
});
