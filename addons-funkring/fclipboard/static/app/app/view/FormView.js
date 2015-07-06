/*global Ext:false*/

Ext.define('Fclipboard.view.FormView', {
    extend: 'Ext.form.FormPanel',    
    xtype: 'formview',
    config: {
       /**
        *  handler for which 
        *  handles saving
        */
       saveHandler: null,
       
       /**
        * default editable
        */
       editable: true,
       
       /**
        * deleteable 
        */
       deleteable: false
    }    
});