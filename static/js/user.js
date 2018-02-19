$(function() {
  var timer;
  $("#search_input").keyup(function() {
    clearTimeout(timer);
    var ms = 10; // milliseconds
    var val = this.value;
    timer = setTimeout(function() {
      search();
    }, ms);
  });
});

function search(){
    var query = document.getElementById("search_input").value;
    console.log(query)
    $.ajax({
        type: 'post',
        data: { 'query': query},
        url: '/search',
        success: function (response) {
            // We get the element having id of display_info and put the response inside it
            $( '#search_result' ).html(response);
        }
    });
}

function reIndex(){
$( "#index_loader" ).show();
$.ajax({
        type: 'get',
        url: '/index',
        success: function (response) {
            console.log("Re-Indexed")
            $( "#index_loader" ).hide();
        }
    });
}