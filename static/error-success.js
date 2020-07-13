setError = function (message) {
    if (error) {
        $("#error").text(message);
        $("#error").show();
    }
    else {
        $("#error").hide();
    }
}

setSuccess = function (message) {
    if (message) {
        $("#success").text(message);
        $("#success").show();
    }
    else {
        $("#success").hide();
    }
}