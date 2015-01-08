/*global Ext:false,alert:false*/

var filterList = Ext.create('Ext.List', {
   flex : 1,
   store: {
     fields: ['name'],
     data: [{"name":"Test1"}]
   },
   itemTpl: '{name}'
});

var productionList = Ext.create('Ext.List', {   
   store: {
     fields: ['name'],
     data: [{"name":"Test1"}]
   },
   itemTpl: '{name}'
});


var selPanel = Ext.create('widget.formpanel',{
   
   items: [{
       xtype: 'fieldset',
       title: 'Produktion',       
       items: [
         {
             xtype: 'hiddenfield',
             name: 'production1',
             value: 0             
         },
         {
             xtype: 'button',
             text: 'Produktion 1: Keine',
             handler: function() {
                 
             }
         }        
       ]       
   }] 
    
});

var navPanel = Ext.create('widget.navigationview',{
    flex : 1,
    items: [
        selPanel
    ]    
});

var graphMenu = Ext.create("widget.toolbar",{
    docked: 'top',
    items : [
    ]    
});

var graphPanel = Ext.create('widget.panel', {
   flex : 2,
   layout: {
      type: 'vbox'
   }, 
   items : [
        graphMenu
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
