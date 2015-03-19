/*global Ext:false*, Fclipboard:false*/

Ext.define('Fclipboard.view.Main', {
    extend: 'Ext.navigation.View',
    xtype: 'main',
    id: 'mainView',
    requires: [
        'Ext.TitleBar', 
        'Ext.TabPanel',
        'Ext.dataview.List',
        'Ext.field.Search'
    ],
    config: {
        // **********************************************************
        // Title
        // **********************************************************
        
        title: 'Arbeitsmappen',
    
        // **********************************************************
        // Define available Items
        // **********************************************************
        
        record: null,        
        recordCreateables: null,
        recordViews: [
            { 
              name:'Arbeitsmappe', 
              type: 'workbook', 
              createable: [null],
              form: 'Fclipboard.view.ItemWorkbookForm'
            }            
        ],
        
        // **********************************************************
        // NavigationBar Items
        // **********************************************************
        
        navigationBar: {
            items: {
                xtype: 'button',
                id: 'saveViewButton',
                text: 'Speichern',
                align: 'right',
                hidden: true,
                action: 'saveView'
            }
        },
        
        
        listeners : {
            activeitemchange : function(view, newCard) {
                var items = view.getInnerItems(),
                    index = items.indexOf(newCard),
                    button = view.down('button[action=saveView]'),
                    action = index === 0 ? 'hide' : 'show';
                button[action]();
            }
        },
        
        // **********************************************************
        // View Items
        // **********************************************************
        
        items: [
            {                
                xtype: 'tabpanel',
                tabBarPosition: 'bottom',      
                id: 'mainPanel',
                
                getTitle : function() {
                    return Ext.getCmp("mainView").getTitle();
                },   
                                        
                items: [   
                    {
                        title: 'Einträge',
                        id: 'itemTab',
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
                                    id: 'newItemButton',
                                    text: 'Neu',
                                    action: 'newItem'      
                                }
                            ]                           
                        },
                        {
                            xtype: 'list',
                            height: '100%',
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
                        id: 'attachmentTab',
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
                        id: 'settingsTab',
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
        self.loadRecord();        
   },
   
      
   loadRecord: function() {
       var self = this;
              
       var title = 'Arbeitsmappen';
       var dataType = null;
       
       var record = self.getRecord();
       var itemData = record !== null ? record.data : null;       
       if (itemData !== null) {
           dataType = itemData.type;
           title = itemData.name;
       } 
       
       var recordCreateables = self.getRecordViews().filter(function(e) {                                
                                for (var i=0; i<e.createable.length; i++) {
                                    if (e.createable[i] === dataType) {
                                        return true;
                                    }
                                }
                                return false;
                             });
       
       // update state       
       self.setTitle(title);                      
       self.setRecordCreateables(recordCreateables);

       // update button state
       Ext.getCmp('newItemButton').setHidden(recordCreateables.length===0);
       
       // load data
       var itemStore =  Ext.StoreMgr.lookup("ItemStore");
       itemStore.load();              
   },
   
   showNewItemSelection: function() {       
        var self = this;
        var recordCreateables = self.getRecordCreateables();        
        if ( recordCreateables.length === 0) { 
            return;
        } 
        else if ( recordCreateables.length === 1) {
           self.fireEvent('createItem', self, recordCreateables[0].type);
        } else {        
            var newItemPicker = Ext.create('Ext.Picker',{
                doneButton: 'Erstellen',
                cancelButton: 'Abbrechen',
                modal: true,
                slots:[{
                    name: 'item_type',
                    title: 'Element',
                    displayField: 'name',
                    valueField: 'type',
                    data: recordCreateables
                }],               
                listeners: {
                    change: function(picker,button) {
                        var val = picker.getValue()['item_type'];
                        self.fireEvent('createItem', self, val);
                    }
                } 
            });
            
            Ext.Viewport.add(newItemPicker);
            newItemPicker.show();
        }
   },

   getItemView: function(item_type) {
        var self = this;
        var recordViews = self.getRecordViews();
        for (var i=0; i<recordViews.length; i++) {
            if (recordViews[i].type === item_type) {
                return recordViews[i];
            }
        }
        return null;
   },
   
   /*
   push: function(view) {
        var self = this;
        if ( view.isEditable() ) {
            Ext.getCmp('saveViewButton').setHidden(false);
        }
        
        self.callParent(arguments);

       
   },
   
   pop: function(view) {
       var self = this;
       self.callParent(arguments);
       Ext.getCmp('saveViewButton').setHidden(true);           
   }*/
   
});
