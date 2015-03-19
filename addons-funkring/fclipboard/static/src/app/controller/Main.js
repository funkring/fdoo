/*global Ext:false*/
Ext.define('Fclipboard.controller.Main', {
    extend: 'Ext.app.Controller',

    config: {
        refs: {
            mainView: '#mainView',
        },
        control: {
            'button[action=newItem]': {
                tap: 'newItem'
            },
            'button[action=saveView]': {
                tap: 'saveRecord'
            },
            mainView: {
                createItem: 'createItem'  
            }
        }
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
                 'parent_id' : record !== null ? record.data._id : null
                });
       
        self.editItem(newItem);
    },
    
    editItem: function(record) {        
        var self = this;
        var mainView = self.getMainView();
        var itemType = record.data.type;
        var itemView = mainView.getItemView(itemType);
        var items = [
            {
                xtype: 'textfield',
                name: 'name',
                label: 'Name',
                required: true
            }
        ];
        
        if (itemType === 'workbook') {
            items.push(
                {
                    xtype: 'selectfield',
                    name: 'partner_id',
                    label: 'Partner',
                    store: 'PartnerStore',
                    valueField: '_id',
                    displayField: 'name'
                }
            );
        }
        self.getMainView().push({
            title: itemView.name,
            xtype: 'formpanel',
            record: record,
            items: items,
            editable: true
        });
    },
    
    saveRecord: function() {
        var self = this;
        var mainView = self.getMainView();
        var view = mainView.getActiveItem();
        var record = view.getRecord();
        if ( record !== null ) {
            var values = view.getValues(); 
            record.set(values);
            record.save();
        }
        mainView.pop();
        mainView.loadRecord();
    }
    
});