function add_response(resp) {
    var current = $('#response').val();
    $('#response').val(current + resp + "\n");
}

$("#execute").click(function() {
    $(this).button("loading");
    $.ajax({
        type: "post",
        url: "/execute",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({command: $("#command").val()}),
        error: function(xhr, status, msg) {
            $("#execute").button("reset");
            add_response("ERROR: " + msg);
        },
        success: function(resp) {
            add_response(resp.response);
            $("#execute").button("reset");
        }
    })
})
