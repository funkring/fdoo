/*global Ext:false*/

Ext.define('Fclipboard.view.Main', {
    extend: 'Ext.navigation.View',
    xtype: 'main',
    requires: [
        'Ext.TitleBar', 
        'Ext.TabPanel'
    ],
    config: {
                        
        // **********************************************************
        // Define available Items
        // **********************************************************
            
        item: null,
        itemParent: null,
        itemCreateables: null,
        itemDef: [
            { 
              name:'Arbeitsmappe', 
              type: 'workbook', 
              createable: [null], 
              items: [
                { 
                    xtype : 'textfield',
                    label : 'Name',
                    name : 'name'
                },
                {
                    xtype : 'select',
                    label : 'Partner',
                    name : 'partner_id',
                    valueField : '_id',
                    displayField : 'name',
                    store : 'PartnerStore'
                }
              ]
            }            
        ],
        
        // **********************************************************
        // View Items
        // **********************************************************
        
        items: [
            {                
                xtype: 'tabpanel',
                tabBarPosition: 'bottom',      
                id: 'tab-panel',
                items: [   
                    {
                        title: 'Einträge',
                        id: 'tab-item',
                        iconCls: 'home',                        
                        items: [{
                            docked: 'top',
                            xtype: 'toolbar',
                            items: [
                                {
                                    xtype: 'searchfield',
                                    placeholder: 'Suche',
                                    name: 'searchfield',
                                    flex: 1
                                },
                                {
                                    xtype: 'button',
                                    id: 'button-item-new',
                                    text: 'Neu'          
                                }
                            ]                           
                        },
                        {
                            xtype: 'list',
                            height: '100%',
                            itemId: 'item-list',
                            store: 'ItemStore',
                            disableSelection:true,
                            cls: 'ItemList',
                            itemTpl: Ext.create('Ext.XTemplate',
                                            '<tpl if="type==\'product_amount\'">',
                                                '<span class="left-col">{name}</span>',
                                                '<input class="right-col" name="item_{id}" type="number" data-index="{sequence}"/>',
                                            '<tpl else>',
                                                '{name}',
                                            '</tpl>')
                            /*
                            itemTpl: Ext.create('Ext.XTemplate',
                                            '<tpl if="type==\'product_amount\'">',
                                                '<span style="width:100%;">{name}</span>',
                                                '<input style="width:100px;margin:0px 10px 0px 10px" name="item_{id}" type="number" data-index="{sequence}"/>',
                                            '<tpl else>',
                                                '{name}',
                                            '</tpl>')
                            /*
                            listeners: {
                                select: function (list, model) {
                                    list.deselect(model);
                                    return false;
                                }                        
                            }*/                     
                                                                    
                        }]                
                    },                   
                    {
                        title: 'Anhänge',
                        id: 'tab-attachment',
                        iconCls: 'action',        
                        items: [
                            {
                                docked: 'top',
                                xtype: 'toolbar',
                                items: [
                                    {
                                        xtype:'spacer',
                                        flex: 1
                                    },                                    
                                    {
                                        xtype: 'button',
                                        id: 'button-attachment-foto',
                                        text: '+Foto',
                                        align: 'right'           
                                    }
                               ]                           
                            }
                        ]
                    },
                    {
                        title: 'Info',
                        id: 'tab-settings',
                        iconCls: 'info',        
                        items: [                           
                        ]
                    }
                ]
            }
        ]
    },
    
    // init
   constructor: function(config) {
        var self = this;
        self.callParent(config);
        self.updateItemState();        
   },
   
   
   updateItemState: function() {
       var self = this;
       
       var item = self.getItem();
       var itemType = null;
       var title = "Arbeitsmappen";
       
       if (item !== null) {
           itemType = item.type;
           title = item.name;
       } 
       
       
       var itemCreateables = self.getItemDef().filter(function(e) {
                                return (itemType in e.createable);
                             });
                             
       self.setItemCreateables(itemCreateables);

       // change button states
       //Ext.getCmp('button-new-item').setHidden(itemCreateables.length===0);
       // set title
       self.getNavigationBar().setTitle(title);
   }
});
