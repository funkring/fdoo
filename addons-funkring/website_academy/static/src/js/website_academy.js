$(document).ready(function () {
    
    // check submitted status
    var already_submitted = false;
    $('input[name="form_send"]').each(function () {
      var $input = $(this);
      if ($input.val() === "1") {
          already_submitted=true;
      }
    });
    
    //bind checkbox and visibility for form
    var bind_checkbox_and_form = function(checkbox_id, form_id, form_active_on_check) {
        var $bind_checkbox_input = $(checkbox_id);
        if ($bind_checkbox_input.length) {
            var $bind_checkbox_form = $(form_id);
            if ($bind_checkbox_form.length) {
                //hide/show function
                var bind_checkbox_show_form = function(visible) {
                   if (visible) {
                    $bind_checkbox_form.removeClass("hidden");
                   } else {
                    $bind_checkbox_form.addClass("hidden");
                   }
                };
                //register for click event
                $bind_checkbox_input.on("click", function(ev) {
                    bind_checkbox_show_form(this.checked===form_active_on_check);                    
                });
                bind_checkbox_show_form($bind_checkbox_input.is(":checked")===form_active_on_check);       
            }
            
        }
    };
    
    bind_checkbox_and_form("#parent_address","#parent_address_input",false);
    bind_checkbox_and_form("#invoice_address","#invoice_address_input",true);
        
    // Default Submit
    $('.a-submit').on("click", function (ev) {
        var $form = $(this).closest("form");
        
        // check if it is empty
        var form_data = {};
        var inputs = $form.serializeArray();
        var has_data = false;
        var is_valid = true;
             
        $.each(inputs, function(i, input) {
          form_data[input.name] = input.value;          
          var $form_input =  $("input[name='"+input.name+"']");
          if (input.value!==null && input.value!=="-" && input.value!=="") {            
            if ($form_input.prop("type") !== "hidden") {
                has_data = true;               
            }                        
          }
        });
        
        //validate
        if (form_data.location_id === null || !has_data) {
            is_valid = false;
        }        
        var $wrongdata_error = $("#wrongdata_error");
        if ($wrongdata_error.length) {
            if ( is_valid ) {
                $wrongdata_error.addClass("hidden");                                   
            } else {
                $wrongdata_error.removeClass("hidden");
            }
        }
               
        // submit on no error
        if (is_valid && !already_submitted) {
            $form.submit();
        }        
    });
        
    // Default Back
    $('.a-back').on("click", function (ev) {
        history.back();
    });  
        
  
});