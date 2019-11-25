/*global openerp:false, instance:false*, _:false, $:false*/
openerp.htmleditor = function(instance, local) {
    instance.web.form.FieldTextHtml.include({
        // overwrite existing widget
        initialize_content: function() {
            var self = this;
            if (!this.get("effective_readonly")) {
                self._updating_editor = false;
                this.$textarea = this.$el.find('textarea');
                var width = ((this.node.attrs || {}).editor_width || 'calc(100% - 4px)');
                var height = ((this.node.attrs || {}).editor_height || 250);
                this.$tinymce = this.$textarea.tinymce({
                    theme:      'modern',
                    width:      width, // width not including margins, borders or padding
                    height:     height, // height not including margins, borders or padding
                    plugins: [
                        'advlist autolink autosave link lists charmap hr anchor pagebreak spellchecker',
                        'searchreplace wordcount visualblocks visualchars code nonbreaking',
                        'table contextmenu directionality paste textcolor colorpicker'
                    ],
                    toolbar: " bold italic underline strikethrough | alignleft aligncenter alignright alignjustify | bullist numlist | outdent indent | hr nonbreaking pagebreak | removeformat | code translate",
                    menubar: false,
                    toolbar_items_size: 'small',
                    setup: function(editor) {
                        editor.on('change', function(e) {                            
                             self.internal_set_value(editor.getContent());
                        });
                        
                        if ( self.field.translate ) {
                            editor.addButton('translate', {
                               tooltip: 'Translate',
                               image : '/web/static/src/img/icons/terp-translate.png',
                               onclick: self.on_translate
                            });
                        }
                    },
                    urlconverter_callback: function(url, node, on_save, name) {                        
                        return url;
                    }
                           
                })[0];
            }
        },
        
        focus: function() {
             var input = !this.get("effective_readonly") && this.$tinymce;
             return input ? input.focus() : false;
        },
        
        render_value: function() {
            if (!this.get("effective_readonly")) {
                this.$textarea.val(this.get('value') || '');
            } else {
                this.$el.html(this.get('value'));
            }
        }       
    });
    
};
 