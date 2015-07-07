/*global Ext:false*, Fclipboard:false*/

Ext.define('Fclipboard.view.Main', {
    extend: 'Ext.navigation.View',
    xtype: 'main',
    id: 'mainView',
    requires: [
        'Ext.TitleBar', 
        'Ext.TabPanel',
        'Ext.dataview.List',
        'Ext.field.Search',
        'Ext.util.DelayedTask',
        'Ext.field.Password',
        'Ext.field.Text'
    ],
    config: {
        // **********************************************************
        // Title
        // **********************************************************
        
        title: 'Dokumente',
    
        // **********************************************************
        // Define available Items
        // **********************************************************
        
        record: null,        
                        
        // **********************************************************
        // NavigationBar Items
        // **********************************************************
        
        navigationBar: {
            items: [
            {
                xtype: 'button',
                id: 'parentItemButton',
                ui: 'back',
                text: 'Back',       
                align: 'left',
                action: 'parentItem'  
            },           
            {
                xtype: 'button',
                id: 'editConfigButton',
                iconCls: 'settings',                
                align: 'right',
                hidden: true,   
                action: 'editConfig'   
            },  
            {
                xtype: 'button',
                id: 'syncButton',
                text: 'Starten',
                //iconCls: 'compose',  
                hidden: true,              
                align: 'right',
                action: 'sync'                
            },
            {
                xtype: 'button',
                id: 'editItemButton',
                iconCls: 'settings',                
                align: 'right',
                action: 'editItem'   
            },    
            {
                xtype: 'button',
                id: 'deleteRecord',
                iconCls: 'trash',
                align: 'right',
                action: 'deleteRecord'  
            },                   
            {
                xtype: 'button',
                id: 'newItemButton',
                iconCls: 'add',
                align: 'right',
                action: 'newItem'      
            },
            {
                xtype: 'button',
                id: 'saveViewButton',
                text: 'OK',
                //iconCls: 'compose',  
                hidden: true,              
                align: 'right',
                action: 'saveView'                
            }           
                         
        ]
        },
        
        
        listeners : {
            activeitemchange : function(view, newCard) {
                var items = view.getInnerItems(),
                    index = items.indexOf(newCard),
                    saveButton = view.down('button[action=saveView]'),
                    newButton = view.down('button[action=newItem]'),
                    editButton = view.down('button[action=editItem]'),
                    backButton = view.down('button[action=parentItem]'),
                    editConfigButton = view.down('button[action=editConfig]'),
                    syncButton = view.down('button[action=sync]'),
                    deleteButton = view.down('button[action=deleteRecord]');
                    
                if ( index === 0) {
                    saveButton.hide();
                    newButton.show();
                    deleteButton.hide();
                } else {
                    // check for deletable support
                    try {
                        if (newCard.getDeleteable() && !newCard.getRecord().phantom ) {
                            deleteButton.show();
                        } else {
                            deleteButton.hide();
                        }
                    } catch (err) {
                        deleteButton.hide();
                    }
                    
                    saveButton.show();
                    newButton.hide();                    
                    editButton.hide();
                    backButton.hide();
                    syncButton.hide();
                    editConfigButton.hide();
                }
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
                
                listeners: {
                    activeitemchange: function(view, value, oldValue, opts) {
                        Ext.getCmp("mainView").validateComponents();  
                    }  
                },
                                        
                items: [   
                    {
                        title: 'Dokumente',
                        id: 'itemTab',
                        iconCls: 'home',                        
                        items: [{
                            docked: 'top',
                            xtype: 'toolbar',
                            items: [                               
                                {
                                    xtype: 'searchfield',
                                    placeholder: 'Suche',
                                    id: 'itemSearch',
                                    flex: 1,
                                    listeners: {
                                        keyup: function(field, key, opts) {
                                            Ext.getCmp("mainView").searchItemDelayed(field.getValue());
                                        },
                                        clearicontap: function() {
                                            Ext.getCmp("mainView").searchItemDelayed(null);
                                        }
                                    }                       
                                }                           
                            ]                           
                        },
                        {
                            xtype: 'list',
                            height: '100%',
                            store: 'ItemStore',
                            id: 'itemList',
                            cls: 'ItemList',
                            itemTpl: Ext.create('Ext.XTemplate',
                                            '<tpl if="type==\'product_amount\'">',
                                                '<span class="left-col">{name}</span>',
                                                '<input class="right-col" name="item_{id}" type="number" data-index="{sequence}"/>',
                                            '<tpl else>',
                                                '{name}',
                                            '</tpl>')                
                        }]            
                    },                                 
                    {
                        title: 'Anhänge',
                        id: 'attachmentTab',
                        iconCls: 'action',        
                        items: [
                            {
                                             
                            }
                        ]
                    },
                    {
                        title: 'Partner',
                        id: 'partnerTab',
                        iconCls: 'team',        
                        items: [{
                            docked: 'top',                            
                            xtype: 'toolbar',
                            items: [                                
                                {
                                    xtype: 'searchfield',
                                    placeholder: 'Suche',
                                    id: 'partnerSearch',
                                    flex: 1,
                                    listeners: {
                                        keyup: function(field, key, opts) {
                                            Ext.getCmp("mainView").searchPartnerDelayed(field.getValue());
                                        },
                                        clearicontap: function() {
                                            Ext.getCmp("mainView").searchPartnerDelayed(null);
                                        }
                                    }
                                }                              
                            ]                           
                        },
                        {
                            xtype: 'list',
                            id: 'partnerList',
                            height: '100%',
                            store: 'PartnerStore',
                            //disableSelection:true,                            
                            cls: 'PartnerList',
                            itemTpl: '{name}'                       
                        }]
                    },
                    {
                        title: 'Hochladen',
                        id: 'syncTab',
                        iconCls: 'refresh',
                        items: [                          
                            {
                                xtype: 'list',
                                id: 'logList',
                                height: '100%',
                                store: 'LogStore',
                                disableSelection:true,                            
                                cls: 'LogList',
                                itemTpl: '{message}'                       
                            }                
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
        
        self.partnerSearchTask = Ext.create('Ext.util.DelayedTask', function() {
            self.searchPartner();
        });
           
        self.itemSearchTask = Ext.create('Ext.util.DelayedTask', function() {
            self.searchItems();
        });
                   
        self.loadRecord();        
   },
   
   searchDelayed: function(task) {
        task.delay(500);
   },
   
   searchPartnerDelayed: function(text) {
        this.partnerSearch = text;
        this.searchDelayed(this.partnerSearchTask);
   },
   
   searchItemDelayed: function(text) {
        this.itemSearch = text;
        this.searchDelayed(this.itemSearchTask);    
   },   
   
   searchPartner: function() {
       var partnerStore = Ext.StoreMgr.lookup("PartnerStore");
       
       if ( !Ext.isEmpty(this.partnerSearch) ) {
         partnerStore.load({
           params: {
               'domain' : [['name','like',this.partnerSearch]]
           }
         });
       } else {
         partnerStore.load();
       }    
   },
   
   searchItems: function() {
       var record = this.getRecord();
       var domain = [['parent_id','=',record !== null ? record.getId() : null]];
       
       if ( !Ext.isEmpty(this.itemSearch) ) {
           domain.push(['name','like',this.itemSearch]);
       }
       
       // load data
       var itemStore = Ext.StoreMgr.lookup("ItemStore");
       itemStore.load({
           params: {
               'domain' : domain
           }
       });  
   },
   
        
   validateComponents: function(context) {
       var self = this;

       // create context
       if (!context) {
           context = {};
       }

       var activeItem = context.activeItem || Ext.getCmp("mainPanel").getActiveItem();
       var title = context.title || activeItem.title;
       var record = context.record || self.getRecord();              
       var data = record && record.data || null;

       var syncTabActive = (activeItem.getId() == "syncTab");
       var itemTabActive = (activeItem.getId() == "itemTab");
       var attachmentTabActive = (activeItem.getId() == "attachmentTab");
       
       // override title with name from data       
       if ( (itemTabActive || attachmentTabActive) && data !== null ) {
           title = data.name;
           if ( attachmentTabActive ) {
               title = title + " / Anhänge ";
           } 
       } 
    
       // update button state
       
       Ext.getCmp('itemSearch').setValue(null);
       Ext.getCmp('partnerSearch').setValue(null);       
       Ext.getCmp('newItemButton').setHidden(syncTabActive);
       Ext.getCmp('editItemButton').setHidden(!itemTabActive || record === null || syncTabActive );
       Ext.getCmp('parentItemButton').setHidden(!itemTabActive || record === null);
       Ext.getCmp('syncButton').setHidden(!syncTabActive);
       Ext.getCmp('editConfigButton').setHidden(!syncTabActive);
       Ext.getCmp('deleteRecord').setHidden(true);
       
       // reset title      
       self.setTitle(title);
       this.getNavigationBar().setTitle(this.getTitle());  
   },
   
      
   loadRecord: function() {
       var self = this;
       
       // init
       self.partnerSearchTask.cancel();
       self.itemSearchTask.cancel();       
       self.partnerSearch = null;
       self.itemSearch = null;
        
       // validate components
       self.validateComponents();
       
       // load data
       self.searchItems();
       self.searchPartner();       
   },
   
   showNewItemSelection: function() {      
        var self = this;
        var activeItem = Ext.getCmp("mainPanel").getActiveItem();
        switch ( activeItem.getId() ) {
            case "itemTab":
                 self.fireEvent('createItem', self, "directory");
                 break;
            case "partnerTab":
                 self.fireEvent('newPartner', self);
                 break;            
            default:
                 break;
        }
        
        
        /*        
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
                        var val = picker.getValue().item_type;
                        self.fireEvent('createItem', self, val);
                    }
                } 
            });
            
            Ext.Viewport.add(newItemPicker);
            newItemPicker.show();
        */
   },

      
   pop: function() {
       this.callParent(arguments);
       this.validateComponents();
   },
   
   leave: function() {
       var self = this;
       self.pop();
       
       var activeItem = Ext.getCmp("mainPanel").getActiveItem();
       var itemTabActive = (activeItem.getId() == "itemTab");
       if ( itemTabActive ) {
          self.fireEvent('parentItem', self);
       } else {
          self.loadRecord();
       }
   }
   
});
