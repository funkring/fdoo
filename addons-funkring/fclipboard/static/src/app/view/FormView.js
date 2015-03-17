/*global Ext:false*/

Ext.define('Fclipboard.view.FormView', {
    extend: 'Ext.form.FormPanel',
    
    config: {
        editable: true
    },
    
    finishView: function() {
        return true;
    },
    
    cancelView: function() {
           
    }    
    
});