// execute when the DOM is fully loaded
$(function() {

    // adapted from http://jsfiddle.net/giorgitbs/52aK9/1/
    // use JS module (function ($) ... (jQuery)) for better compression, runtime
    (function ($) {

       $('#search').keyup(function () { 

            var results = new RegExp($(this).val(), 'i');
            $('.searchable tr').hide();
            $('.searchable tr').filter(function () {
                return results.test($(this).text());
            }).show();

        })

    }(jQuery));

    // refresh process_table every five seconds
    setInterval(process_table, 5000);

    // on click refresh log_table
    $("#log_submit").click(function() {
        log_table();
    });

    // fade alerts in and out http://jsfiddle.net/mfX57/
    $(".alert").fadeTo(2000, 500).slideUp(500, function(){
        $(".alert").alert('close');
    });
});

/**
 * Updates process_table.
 */
function process_table() {

    // get process parameters from selectors
    var parameters = {
        host: $("#host").val(),
        username: $("#user").val()
    };
    
    // refresh table
    $("#process_table").bootstrapTable('refresh', {
            url: '/api/processes',
            query: parameters,
            silent: true
    });
}

/**
 * Updates log_table.
 */
function log_table() {

    // get log_table parameters from selectors
    var parameters = {
        path: $("#path option:selected").text(),
        pattern: $("#pattern").val(),
        host: $("#host").val(),
        username: $("#user").val()
    };

    // refresh data
    $("#log_table").bootstrapTable('refresh', {
            url: '/api/logs',
            query: parameters,
            silent: true
    });

    // ensure form stays filled out post-submit
    jQuery.each(parameters, function(k, v) {
        if (v && k != 'path')
        {
            $("#" + k).val(v);
        }    
    });
}
