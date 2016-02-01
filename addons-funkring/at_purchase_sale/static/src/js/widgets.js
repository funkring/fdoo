/*global openerp:false, instance:false*, _:false, $:false*/

openerp.at_purchase_sale = function(instance, local) {

    /**
     * override get rows
     */
    instance.stock.PickingEditorWidget.include({
    
       renderElement: function(){
            var self = this;
            this._super();
            
            this.$('.js_print_delivery').click(function(){ self.getParent().print_delivery(); });
            this.$('.js_print_shipping').click(function(){ self.getParent().print_shipping(); });
            
            this.$('.js_plus_qty').click(function(){
                var id = $(this).data('product-id');
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().scan_product_id(id,true,op_id);
            });
            
            this.$('.js_minus_qty').click(function(){
                var id = $(this).data('product-id');
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().scan_product_id(id,false,op_id);
            });
            
            this.$('.js_plus_package').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().add_package(op_id, 1);
            });
            
            this.$('.js_minus_package').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().add_package(op_id, -1);
            });
            
            this.$('.js_package').focus(function(){
                self.getParent().barcode_scanner.disconnect();
            });
            this.$('.js_package').blur(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                var value = parseInt($(this).val(),10);
                if (value>=0){
                    self.getParent().set_package_count(value, op_id);
                }
                self.getParent().barcode_scanner.connect(function(ean){
                    self.getParent().scan(ean);
                });
            });
       },
    
       get_rows: function(){
            var model = this.getParent();
            this.rows = [];
            var self = this;
            var pack_created = [];
            _.each( model.packoplines, function(packopline){
                    var pack;
                    var color = "";
                    if (packopline.product_id[1] !== undefined){ pack = packopline.package_id[1];}
                    if (packopline.product_qty == packopline.qty_done){ color = "success "; }
                    if (packopline.product_qty < packopline.qty_done){ color = "danger "; }
                    //also check that we don't have a line already existing for that package
                    if (packopline.result_package_id[1] !== undefined && $.inArray(packopline.result_package_id[0], pack_created) === -1){
                        var myPackage = $.grep(model.packages, function(e){ return e.id == packopline.result_package_id[0]; })[0];
                        self.rows.push({
                            cols: { product: packopline.result_package_id[1],
                                    name: packopline.name,
                                    qty: '',
                                    rem: '',
                                    package_count: '',
                                    package_calc: '',
                                    uom: undefined,
                                    lot: undefined,
                                    pack: undefined,
                                    container: packopline.result_package_id[1],
                                    container_id: undefined,
                                    loc: packopline.location_id[1],
                                    dest: packopline.location_dest_id[1],
                                    id: packopline.result_package_id[0],
                                    product_id: undefined,
                                    can_scan: false,
                                    head_container: true,
                                    processed: packopline.processed,
                                    package_id: myPackage.id,
                                    ul_id: myPackage.ul_id[0],
                            },
                            classes: ('success container_head ') + (packopline.processed === "true" ? 'processed hidden ':''),
                        });
                        pack_created.push(packopline.result_package_id[0]);
                    }
                    self.rows.push({
                        cols: { product: packopline.product_id[1] || packopline.package_id[1],
                                name: packopline.name,
                                qty: packopline.product_qty,
                                rem: packopline.qty_done,
                                package_count: packopline.package_count,
                                package_calc: packopline.package_calc,
                                uom: packopline.product_uom_id[1],
                                lot: packopline.lot_id[1],
                                pack: pack,
                                container: packopline.result_package_id[1],
                                container_id: packopline.result_package_id[0],
                                loc: packopline.location_id[1],
                                dest: packopline.location_dest_id[1],
                                id: packopline.id,
                                product_id: packopline.product_id[0],
                                can_scan: packopline.result_package_id[1] === undefined ? true : false,
                                head_container: false,
                                processed: packopline.processed,
                                package_id: undefined,
                                ul_id: -1,
                        },
                        classes: color + (packopline.result_package_id[1] !== undefined ? 'in_container_hidden ' : '') + (packopline.processed === "true" ? 'processed hidden ':''),
                    });
            });
            //sort element by things to do, then things done, then grouped by packages
            var group_by_container = _.groupBy(self.rows, function(row){
                return row.cols.container;
            });
            var sorted_row = [];
            if (group_by_container.undefined !== undefined){
                group_by_container.undefined.sort(function(a,b){return (b.classes === '') - (a.classes === '');});
                $.each(group_by_container.undefined, function(key, value){
                    sorted_row.push(value);
                });
            }

            $.each(group_by_container, function(key, value){
                if (key !== 'undefined'){
                    $.each(value, function(k,v){
                        sorted_row.push(v);
                    });
                }
            });

            return sorted_row;
        }        
        
    });
   
        
    /**
     * override product scan
     */
    instance.stock.PickingMainWidget.include({
               
        scan: function(ean){ //scans a barcode, sends it to the server, then reload the ui
            var self = this;
            
            var m = /SP([0-9]+)/.exec(ean);
            if ( m ) {
                var i, len, picking;
                var picking_id = parseInt(m[1], 10);    
                                     
                //self.refresh_ui(picking_id);   
                for(i = 0, len = self.pickings.length; i < len; i++){                        
                    if(self.pickings[i] === picking_id) {
                        this.refresh_ui(picking_id);
                        break;
                    }
                }
            }
            
            return self._super(ean);
        },
        
        add_package: function(op_id, increment) { 
            var self = this;
            return new instance.web.Model('stock.picking')
                .call('add_package', [self.picking.id, op_id, increment])
                .then(function(result){
                    return self.refresh_ui(self.picking.id);
                });
        },
        
        print_shipping: function(){
            var self = this;
            return new instance.web.Model('stock.picking').call('print_shipping',[[self.picking.id]])
                   .then(function(action){
                        return self.do_action(action);
                   });
        },
        
        print_delivery: function(){
            var self = this;
            return new instance.web.Model('stock.picking').call('print_delivery',[[self.picking.id]])
                   .then(function(action){
                        return self.do_action(action);                        
                   });
        },
        
        set_package_count: function(package_count, op_id){
            var self = this;
            if(package_count >= 0){
                return new instance.web.Model('stock.pack.operation')
                    .call('write',[[op_id],{'package_count': package_count }])
                    .then(function(){
                        self.refresh_ui(self.picking.id);
                    });
            }
        }
                
    });
    
      
    /**
     * override picking scan
    */
    instance.stock.PickingMenuWidget.include({
    
        on_scan: function(barcode) {
                var self = this;
                
                var m = /SP([0-9]+)/.exec(barcode);
                var i, len, picking;
                
                if ( m ) {
                    var picking_id = parseInt(m[1],10);                    
                    for(i = 0, len = this.pickings.length; i < len; i++){                        
                        picking = this.pickings[i];                    
                        if(picking.id === picking_id) {
                            this.goto_picking(picking.id);
                            break;
                        }
                    }
                } else {                
                    for(i = 0, len = this.pickings.length; i < len; i++){
                        picking = this.pickings[i];                    
                        if(picking.name.toUpperCase() === $.trim(barcode.toUpperCase())){
                            this.goto_picking(picking.id);
                            break;
                        }
                    }
                }
                this.$('.js_picking_not_found').removeClass('hidden');
    
                clearTimeout(this.picking_not_found_timeout);
                this.picking_not_found_timeout = setTimeout(function(){
                    self.$('.js_picking_not_found').addClass('hidden');
                },2000);
    
        }
        
    });
    
};