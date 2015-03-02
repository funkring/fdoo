/*global Ext:false*/

Ext.define('Fclipboard.view.Main', {
    extend: 'Ext.tab.Panel',
    xtype: 'main',
    requires: [
        'Ext.TitleBar'
    ],
    config: {          
        tabBarPosition: 'bottom',       
        items: [
            {
                title: 'Einträge',
                iconCls: 'home',
              
                items: [{
                    docked: 'top',
                    xtype: 'titlebar',
                    title: 'Einträge',
                    items: [
                    {
                        xtype: 'searchfield',
                        placeholder: 'Suche',
                        name: 'searchfield'
                    },
                    {
                        xtype: 'button',
                        text: 'Neu',
                        align: 'right'                            
                    }]
                    
                },{
                    xtype: 'list',
                    height: "100%",
                    itemId: 'itemList',
                    store: 'Items',
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
                iconCls: 'action',

                items: [
                    {
                        docked: 'top',
                        xtype: 'titlebar',
                        title: 'Anhänge'
                    }
                ]
            }
        ]
    },
    
    // init
   constructor: function(config) {
        this.callParent(config);
   }
});
