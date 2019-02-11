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

function set_memtier_response(resp) {
    $('#memtier_response').text(resp + "\n");
}

$("#memtier_start").click(function() {
    $("#memtier_start").button("loading");
    set_memtier_response("");
    $.ajax({
        type: "post",
        url: "/memtier_benchmark/start",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({args: $("#arguments").val()}),
        error: function(xhr, status, msg) {
            $("#memtier_start").button("reset");
            set_memtier_response("ERROR: " + msg);
        },
        success: function(resp) {
            set_memtier_response(resp.response);
        }
    })
})

$("#memtier_poll").click(function() {
    $("#memtier_poll").button("loading");
    set_memtier_response("");
    $.ajax({
        type: "get",
        url: "/memtier_benchmark/poll",
        error: function(xhr, status, msg) {
            $("#memtier_poll").button("reset");
            $("#memtier_start").button("reset");
            set_memtier_response("ERROR: " + msg);
        },
        success: function(resp) {
            set_memtier_response(resp.response[1]);
            $("#memtier_poll").button("reset");
            if (resp.response[0]) {
                $("#memtier_start").button("reset");
            }
        }
    })
})

$("#memtier_stop").click(function() {
    $("#memtier_stop").button("loading");
    set_memtier_response("");
    $.ajax({
        type: "post",
        url: "/memtier_benchmark/stop",
        error: function(xhr, status, msg) {
            $("#memtier_stop").button("reset");
            set_memtier_response("ERROR: " + msg);
        },
        success: function(resp) {
            set_memtier_response(resp.response);
            $("#memtier_stop").button("reset");
            $("#memtier_start").button("reset");
        }
    })
})
