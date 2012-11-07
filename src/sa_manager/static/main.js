(function($){
  $(document).ready(function() {

    // Turn any table into a Bootstrapping dataTable on page load
    $('.container table').dataTable({
      "sDom": "<'row'<'span6'l><'span6'f>r>t<'row'<'span6'i><'span6'p>>",
      "sPaginationType": "bootstrap",
      "oLanguage": {
        "sLengthMenu": "_MENU_ records per page"
      }
    });
  });
})(jQuery);