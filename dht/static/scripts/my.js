function printer(id, data) {
//    var pp = JSON.parse(data);
    document.getElementById(id).innerHTML = data.data;
}

function pause(id) {
//    var pp = JSON.parse(data);
    document.getElementById(id).innerHTML = "Loading...";
}
    
function get (url, event, cb_pause, callback, param, param2) {
    cb_pause(param);
    event.preventDefault();
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'json';
    
    xhr.onload = function () {
        console.log(xhr);
        var status = xhr.status;

        if (status == 200) {
            callback(param2, xhr.response);
        } else {
            callback("FAILURE " + status);
        }
    };

    xhr.send();
}
