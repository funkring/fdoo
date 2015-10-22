/*global openerp:false, instance:false*, _:false, $:false*/

openerp.sale_purchase_quotation = function(instance, local) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
  
   
    local.PurchaseQuotationWidget = instance.web.form.FormWidget.extend(instance.web.form.ReinitializeWidgetMixin, {
        events: {
        
        },
        init: function() {
            this._super.apply(this, arguments);
            var self = this;
            
            self.set({
                quotations: []
            });
            
            //self.updating = false;
            //self.querying = false;
            self.field_manager.on("field_changed:quotation_ids", self, self.query_quotations);            
            self.field_manager.on("field_changed:supplier_id", self, self.initialize_content);
            self.field_manager.on("field_changed:quotation_active", self, self.initialize_content);
            
            self.dm_query_quotation = new instance.web.DropMisordered();
            self.dm_execute = new instance.web.DropMisordered();
        },
        
        initialize_field: function() {
            var self = this;
            instance.web.form.ReinitializeWidgetMixin.initialize_field.call(self);
            self.on("change:quotations", self, self.initialize_content);
        },
        
        initialize_content: function() {        
            var self = this;
            var selected_supplier_id = self.field_manager.get_field_value('supplier_id');           
            var quotations = [];  
            var quot_sent = 0;
            
            _.each(self.get("quotations"), function(quotation) {
                var partner_id = quotation.partner_id && quotation.partner_id[0] || null;
                if ( quotation.quot_sent ) {
                    quot_sent++;
                }                
                quotations.push({
                    id: quotation.id,            
                    partner_id: partner_id,
                    partner: quotation.partner_id && quotation.partner_id[1] || '',
                    price_unit: instance.web.format_value(quotation.price_unit, { type:"float" }),
                    pricelist_price: instance.web.format_value(quotation.pricelist_price, { type:"float" }),
                    quot_selected: partner_id ===  selected_supplier_id,
                    quot_sent: quotation.quot_sent,
                    state: quotation.state
                    
                });
            });
            
            self.quotation_active =self.field_manager.get_field_value('quotation_active') || false;
            self.quotation_all = (quot_sent === quotations.length);
            self.quotations = quotations;
            self.$el.html(QWeb.render("sale_purchase_quotation.PurchaseQuotation", {widget: self}));
            
            // add listener       
            //self.$(".oe_purchase_quotation_select").click(_.bind(self.select_supplier, self));
            self.$(".oe_purchase_quotation_select").click(function(ev) {
                var data_supplier_id = $(this).attr('data-supplier-id');
                if ( data_supplier_id ) {
                    var suppier_id = parseInt(data_supplier_id, 10);
                    self.field_manager.set_values({"supplier_id":suppier_id});
                    self.view.recursive_save();
                }
            });
            
            self.$('.oe_purchase_quotation_price_input').change(function() {
                var value = instance.web.parse_value($(this).val(), { type:"float" });
                var purchase_line_id = parseInt($(this).attr('data-quotation-id'), 10);
                //debugger;
                if ( purchase_line_id ) {
                    var commands = self.field_manager.get_field_value("quotation_ids");
                    _.each(commands, function(cmd) {
                        if ( cmd[1] == purchase_line_id ) {
                            cmd[0] = 1;
                            cmd[2] = {price_unit:value};
                            
                        }
                    });
                    self.field_manager.set_values({quotation_ids:commands});
                }
            });

            // create button            
            var quotation_create_button = self.$('.oe_purchase_quotation_create');  
            quotation_create_button.attr('disabled',!self.view.is_interactible_record());
            quotation_create_button.click(function() {
                self.view.recursive_save().then(function() {
                    // build action data
                    var action_data = {
                       name: "start_quotation",
                       type: "object"
                    };
                    
                    // call action
                    self.view.do_execute_action(action_data, self.view.dataset, self.view.datarecord.id, function() {
                       self.view.recursive_reload();
                    });                    
                    
                });
            });
                
            self.$('.oe_purchase_quotation_send_all').click(function() {
                self.view.recursive_save().then(function() {
                    // execute quotation create
                    self.dm_execute.add(new instance.web.Model(self.view.model).call("send_mail_supplier", [self.view.dataset.ids, new instance.web.CompoundContext()]).done(function(result) {
                        if ( result && typeof(result) === 'object' ) {
                            self.do_action(result);
                        }
                    }));
                });
            });
            
             self.$('.oe_purchase_quotation_send_one').click(function() {             
                var purchase_line_id = $(this).attr('data-quotation-id');
                self.view.recursive_save().then(function() {
                    if ( purchase_line_id ) {
                        purchase_line_id = parseInt(purchase_line_id,10);
                        // execute quotation create
                        self.dm_execute.add(new instance.web.Model('purchase.order.line').call("send_mail_supplier_one", [[purchase_line_id], new instance.web.CompoundContext()]).done(function(result) {
                            if ( result && typeof(result) === 'object' ) {                                
                                self.do_action(result);
                            }
                        }));
                    }
                });
            });
                
            
        }, 
                        
        query_quotations: function() {
            var self = this;
            var commands = this.field_manager.get_field_value("quotation_ids");
            self.dm_query_quotation.add(new instance.web.Model(self.view.model).call("resolve_2many_commands", ["quotation_ids", 
                commands, [],
                new instance.web.CompoundContext() ])).done(function(result) {
                     self.set({'quotations' : result});
                });
            
        }
        
    });
  
    instance.web.form.custom_widgets.add('purchase_quotation', 'instance.sale_purchase_quotation.PurchaseQuotationWidget');
    
};