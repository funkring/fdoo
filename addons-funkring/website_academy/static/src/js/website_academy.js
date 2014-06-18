$(document).ready(function () {
    //handle parent address
    var $parent_address = $("#parent_address");
    if ($parent_address !== null) {
        $parent_address.on("click", function (ev) {
            var address_input = $("#parent_address_input");
            if (this.checked) {            
                address_input.addClass("hidden");
            }  else {
                address_input.removeClass("hidden");
            }
        });      
    }

    //handle invoice address
    var $invoice_address = $("#invoice_address");
    if ($invoice_address !== null) {
        $invoice_address.on("click", function (ev) {
            var address_input = $("#invoice_address_input");
            if (this.checked) {
                address_input.removeClass("hidden");
            }  else {
                address_input.addClass("hidden");
            }
        });   
    }
    
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
        if ($wrongdata_error !== null) {
            if ( is_valid ) {
                $wrongdata_error.addClass("hidden");                                   
            } else {
                $wrongdata_error.removeClass("hidden");
            }
        }
               
        // submit on no error
        if (is_valid) {
            $form.submit();
        }        
    });
        
    // Default Back
    $('.a-back').on("click", function (ev) {
        history.back();
    });  
        
  
});