/*global openerp:false, instance:false*, _:false, $:false*/

openerp.at_purchase_sale = function(instance, local) {

    /**
     * override get rows
     */
    instance.stock.PickingEditorWidget = instance.stock.PickingEditorWidget.extend({
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
    instance.stock.PickingMainWidget = instance.stock.PickingMainWidget.extend({
               
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
        }
                
    });
    
      
    /**
     * override picking scan
    */
    instance.stock.PickingMenuWidget = instance.stock.PickingMenuWidget.extend({
    
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