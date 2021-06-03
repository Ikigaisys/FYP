function printer(id, data) {
    var pp = JSON.parse(data);
    document.getElementById(id).innerHTML = pp.data;
}

function get (url, callback, param) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'json';
    
    xhr.onload = function () {
        console.log(xhr);
        var status = xhr.status;

        if (status == 200) {
            callback(param, xhr.response);
        } else {
            callback("FAILURE " + status);
        }
    };

    xhr.send();
}
