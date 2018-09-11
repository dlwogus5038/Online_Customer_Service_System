function staff_detail(data, id, counter) {
    var msg,
        msg = replace_em(String(data))
    var new_msg = ""
    var check_par = 0
    if (msg[0] === '{') {
        for (var i = 0; i < msg.length; i++) {
            if (msg[i] === '}' && check_par === 0) {
                new_msg = ""
                check_par = 1
            }
            else {
                new_msg += msg[i]
            }
        }
    }
    else {
        new_msg = msg
    }

    if (new_msg[0] === '*' && new_msg[1] === 'l' &&
        new_msg[2] === 'o' && new_msg[3] === 'g' && new_msg[4] === '*') {
        var image_path = ""
        for (var i = 0; i < new_msg.length; i++) {
            if (new_msg[i] === '*') {
                image_path = ""
            }
            else {
                image_path += new_msg[i]
            }
        }
        image_path = 'static/staff_image/' + image_path
        var image_label = '<img src = ' + image_path + ' height = "200" style="margin-right:7px" >'
        $("#staff_send" + String(id) + "0" + String(counter)).append(image_label)
    }
    else {
        new_msg = '<div class="text">' + new_msg + '</div>'
        $("#staff_send" + String(id) + "0" + String(counter)).append(new_msg)
    }
}

function user_detail(data, id, counter) {
    var msg
    msg = replace_em(String(data))
    if (msg[0] === '*' && msg[1] === 'l' &&
        msg[2] === 'o' && msg[3] === 'g' && msg[4] === '*') {
        var image_path = ""
        for (var i = 0; i < msg.length; i++) {
            if (msg[i] === '*') {
                image_path = ""
            }
            else {
                image_path += msg[i]
            }
        }
        image_path = 'static/user_image/' + image_path
        var image_label = '<img src = ' + image_path + ' height = "200">'

        $("#staff_send" + String(id) + "1" + String(counter)).append(image_label)
    }
    else {
        msg = '<div class="text">' + msg + '</div>'
        $("#staff_send" + String(id) + "1" + String(counter)).append(msg)
    }
}