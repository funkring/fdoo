/*global openerp:false, instance:false*, _:false, $:false*/

openerp.at_delivery = function(instance, local) {

    /**
     * override done
     */
    instance.stock.PickingMainWidget.include({               
        carrier_label: function() {
            var self = this;
            return new instance.web.Model('stock.picking').call('action_carrier_label', [[self.picking.id], new instance.web.CompoundContext()])
                .then(function(action){
                    if ( typeof action == 'object') {
                        return self.do_action(action);
                    } else {
                        return 0;
                    }
                });
        },
               
        done: function(){
            var self = this;
            return new instance.web.Model('stock.picking')
                .call('action_done_from_ui',[self.picking.id, {'default_picking_type_id': self.picking_type_id}])
                .then(function(new_picking_ids){
                    self.carrier_label().then(function() {
                        if (new_picking_ids){
                            return self.refresh_ui(new_picking_ids[0]);
                        }
                        else {
                            return 0;
                        }
                    });
                });
        }
                
    });
    
    
};