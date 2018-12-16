function set_response(resp) {
    $('#response').text(resp + "\n");
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
            set_response("ERROR: " + msg);
        },
        success: function(resp) {
            set_response(resp.response);
            $("#execute").button("reset");
        }
    })
})

function set_masters_response(resp) {
    $('#masters_response').text(resp + "\n");
}

$("#masters").click(function() {
    $(this).button("loading");
    $.ajax({
        type: "get",
        url: "/masters",
        error: function(xhr, status, msg) {
            $("#masters").button("reset");
            set_masters_response("ERROR: " + msg);
        },
        success: function(resp) {
            let value = "Host: " + resp.response[0] + " Port: " + resp.response[1]
            set_masters_response(value);
            $("#masters").button("reset");
        }
    })
})
