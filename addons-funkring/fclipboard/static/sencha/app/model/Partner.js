/*global Ext:false*/
Ext.define('Fclipboard.model.Partner', {
   extend: 'Ext.data.Model',
   requires: [
       'Ext.proxy.PouchDB'
   ],
   config: {
       fields: ['name', 
                'email',
                'mobile',
                'phone',
                'street',
                'sreet2',
                'zip', 
                'city',
                'fax'            
                ],
       identifier: 'uuid',
       proxy: {           
            type: 'pouchdb',
            database: 'fclipboard',
            domain: [['fdoo__ir_model','=','res.partner']]      
        }
   } 
});