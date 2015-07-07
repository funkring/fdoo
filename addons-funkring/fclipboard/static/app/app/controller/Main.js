/*global Ext:false, PouchDB:false, PouchDBDriver:false, openerplib:false */
Ext.define('Fclipboard.controller.Main', {
    extend: 'Ext.app.Controller',
    requires: [
        'Ext.field.Hidden',
        'Ext.field.Select',
        'Ext.form.FieldSet',
        'Ext.proxy.PouchDBDriver'
    ],
    config: {
        refs: {
            mainView: '#mainView',
            mainPanel: '#mainPanel',
            partnerList: '#partnerList',
            itemList: '#itemList'
        },
        control: {
            'button[action=editItem]': {
                tap: 'editCurrentItem'   
            },
            'button[action=newItem]': {
                tap: 'newItem'
            },
            'button[action=saveView]': {
                tap: 'saveRecord'
            },            
            'button[action=parentItem]': {
                tap: 'parentItem'  
            },
            'button[action=sync]': {
                tap: 'sync'  
            },
            'button[action=editConfig]' : {
                tap: 'editConfig'
            },
            'button[action=deleteRecord]' : {
                tap: 'deleteRecord'  
            },
            mainView: {
                createItem: 'createItem',
                newPartner: 'newPartner',
                parentItem: 'parentItem'
            },
            partnerList: {
                select: 'selectPartner'
            },
            itemList: {
                select: 'selectItem'
            }
        }
    },
    
    init: function() {
        var self = this;        
        self.callParent(arguments);
        self.path = [];  
    },

    newItem: function() {
        this.getMainView().showNewItemSelection();
    },
    
    createItem: function(view, item_type) {
        var self = this;
        var mainView = self.getMainView();
        var record = mainView.getRecord();
        
        var newItem = Ext.create('Fclipboard.model.Item',
                {'type': item_type,
                 'parent_id' : record !== null ? record.getId() : null
                });
       
        self.editItem(newItem);
    },
    
    editCurrentItem: function() {
        var mainView = this.getMainView();
        var record = mainView.getRecord();
        if ( record ) {
            this.editItem(mainView.getRecord());
        } 
    },
           
    editItem: function(record) {        
        var self = this;
        var items = {
            xtype: 'textfield',
            name: 'name',
            label: 'Name',
            required: true
        };
            
        // new view
        self.getMainView().push({
            title: record.data.name,
            xtype: 'formview',
            record: record,
            items: items,
            editable: true,
            deleteable: true
        });
        
    },
        
    newPartner: function() {        
        var newPartner = Ext.create('Fclipboard.model.Partner',{});       
        this.editPartner(newPartner);
    },
    
    editPartner: function(record) {
        var self = this;       
        self.getMainView().push({
            title: 'Partner',
            xtype: 'partnerform',
            record: record,
            deleteable: true
        });
    },
    
    editConfig: function(record) {
        var self = this;
        var db = PouchDBDriver.getDB('fclipboard');
        
        var load = function(doc) {
            var configForm = Ext.create("Fclipboard.view.ConfigView",{
                title: 'Konfiguration',
                xtype: 'configform',
                saveHandler: function(view, callback) {
                    var newValues = view.getValues();
                    newValues._id = '_local/config';
                    db.put(newValues).then( function() {
                         callback();
                    });
                }
            });

            configForm.setValues(doc);                    
            self.getMainView().push(configForm);
        };
        
        db.get('_local/config').then( function(doc) {
            load(doc);
        }).catch(function (error) {
            load({});
        });        
        
    },
    
    saveRecord: function() {
        var self = this;
        var mainView = self.getMainView();
        var view = mainView.getActiveItem();
        
        // check for save handler
        var saveHandler = null;
        try { 
            saveHandler = view.getSaveHandler();
        } catch (err) {            
        }        
        
        var reloadHandler = function(err) {
            mainView.pop();
            mainView.loadRecord();
        };
        
        // if save handler exist use it
        if ( saveHandler ) {
            saveHandler(view, reloadHandler);          
        } else {
            // otherwise try to store record
            var record = view.getRecord();
            if ( record !== null ) {
                var values = view.getValues(); 
                record.set(values);
                record.save();
            }
            reloadHandler();
        }
    },
    
    deleteRecord: function() {
        var self = this;
        var record = self.getMainView().getActiveItem().getRecord();

        if ( record !== null ) {
            Ext.Msg.confirm('Löschen', 'Soll der ausgewählte Datensatz gelöscht werden?', function(choice)
            {
               if(choice == 'yes')
               {                    
                   var db = self.getDB();
                   db.get( record.getId() ).then( function(doc) { 
                        doc._deleted=true;
                        db.put(doc).then( function() {
                           self.getMainView().leave();
                        });
                   });
                       
               }         
            });
        }
        
    },
        
    
    selectPartner: function(list, record) {
        list.deselect(record);
        this.editPartner(record);
        return false;                                
    },
    
    selectItem: function(list, record) {
        list.deselect(record);
        var mainView = this.getMainView();
        
        var lastRecord = mainView.getRecord();
        if (lastRecord !== null) {
            this.path.push(lastRecord);
        }
        
        mainView.setRecord(record);
        mainView.loadRecord();
        return false;
    },
    
    parentItem: function() {
        var parentRecord = null;
        if ( this.path.length > 0 ) {
            parentRecord = this.path.pop();           
        } 
        var mainView = this.getMainView();
        mainView.setRecord(parentRecord);
        mainView.loadRecord();
    },

    getDB: function() {
        var db = PouchDBDriver.getDB('fclipboard');
        return db;
    },

    sync: function() {        
        var self = this;
        var db = self.getDB();
        
        db.get('_local/config').then( function(config) {
            var log = Ext.getStore("LogStore");
            log.info("Hochladen auf <b>" + config.host + ":" + config.port + "</b> mit Benutzer <b>" + config.user +"</b>");
            // reload after sync
            PouchDBDriver.syncOdoo(config, [Ext.getStore("PartnerStore")], log, function(res, doc) {
                 mainView.loadRecord();
            });
        });        
       
    }
    
});