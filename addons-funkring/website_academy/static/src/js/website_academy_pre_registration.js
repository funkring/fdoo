$(document).ready(function () {
    // Default Submit
    $('.a-submit').on("click", function (ev) {
        $(this).closest('form').submit();
    });    
});