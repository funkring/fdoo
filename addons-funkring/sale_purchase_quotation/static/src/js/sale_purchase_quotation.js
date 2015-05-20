openerp.sit_sale_pre_purchase_quotation = function (instance) {
    instance.web.FormView.include({
        reload: function() {
            var self = this;
            return this.reload_mutex.exec(function() {
                if (self.dataset.index === null || self.dataset.index === undefined) {
                    self.trigger("previous_view");
                    return $.Deferred().reject().promise();
                }
                if (self.dataset.index < 0) {
                    return $.when(self.on_button_new());
                } else {
                    var fields = _.keys(self.fields_view.fields);
                    fields.push('display_name');
                    return self.dataset.read_index(fields,
                        {
                            context: {
                                'bin_size': true,
                                'future_display_name': true
                            },
                            check_access_rule: true
                        }).then(function(r) {
                            if (self.dataset.model == 'sale.order.line' && self.dataset.ids[self.dataset.index] > 0)  {
                                var ds = new instance.web.DataSetSearch(self, self.dataset.model, {}, [['id', '=', self.dataset.ids[self.dataset.index]]]);
                                return ds.read_slice([]
                                ).then(function(rec) {
                                    self.trigger('load_record', rec[0]);
                                    self.dataset.parent_view.recursive_reload();
                                })
                            }
                            else{
                                self.trigger('load_record', r);
                            }
                        }).fail(function (){
                            self.do_action('history_back');
                        });
                }
        });
    },
    });
};
