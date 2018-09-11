var socket
var date = new Date()
var time = []
var usernum = "1"
var proNum
var isConnect = []
var user_IP = []
var push_evaluation_msg = "请对我的工作进行评价"
var push_evaluation_num = []
$(function () {
    for (var i = 1; i <= proNum; i++) {
        $('#emotion' + String(i)).qq_face({
            id: 'facebox',
            assign: 'InputMessage' + String(i),
            path: 'static/images/arclist/'
        })
    }
})

function replace_em(str) {
    str = str.replace(/\</g, '&lt;')
    str = str.replace(/\>/g, '&gt;')
    str = str.replace(/\n/g, '<br/>')
    str = str.replace(/\[em_([0-9]*)\]/g, '<img src="static/images/arclist/$1.gif" border="0" />')
    return str
}

function init(code) {
    var host = "ws://127.0.0.1:" + code + '/'
    try {
        socket = new WebSocket(host)
        socket.onopen = function (msg) {
            for (var i = 1; i <= proNum; i++) {
                user_IP[i] = "0.0.0.0"
                time[i] = "0" + ":" + "0"
                log("Begin Connection!", i)
            }
        }
        socket.onmessage = function (msg) {
            var json_data = check_num(msg.data)
            var num = json_data.num
            var new_msg = json_data.msg
            log(new_msg, num)
        }
        socket.onclose = function (msg) {
            for (var i = 1; i <= proNum; i++) {
                log("Lose Connection!", i)
                isConnect[i] = 0
            }
        }
    }
    catch (ex) {
        for (var i = 1; i <= proNum; i++) {
            log(ex, i)
        }
    }
    document.getElementById("InputMessage" + usernum).focus()
}

function check_num(msg) {
    var num = ""
    var new_msg = ""
    var i = 0

    if (msg[0] !== '{') {
        return {
            'num': usernum,
            'msg': msg
        }
    }

    for (i = 0; ; i++) {
        if (msg[i] === '{') {
            continue
        }
        else if (msg[i] === '}') {
            break
        }
        else {
            num += msg[i]
        }
    }

    var check_msg_num = 0
    for (i = 0; ; i++) {
        if (msg[i] === '}' && check_msg_num === 0) {
            new_msg = ""
            check_msg_num = 1
        }
        else if (i === msg.length) {
            break
        }
        else {
            new_msg += msg[i]
        }
    }

    return {
        'num': num,
        'msg': new_msg
    }
}

function send(num) {
    if (isConnect[num] === 1) {
        var txt, msg
        txt = document.getElementById("InputMessage" + num)
        msg = '{' + num + '}'
        msg += txt.value
        if (!txt.value) {
            alert("Message can not be empty")
            return
        }
        txt.value = ""
        txt.focus()
        try {
            socket.send(msg)
        } catch (ex) {
            for (var i = 1; i <= proNum; i++) {
                log(ex, i)
            }
        }
        var json_data = check_num(msg)
        log_user_message(json_data.msg, usernum)
    }
}

window.onbeforeunload = function () {
    try {
        socket.send('quit')
        socket.close()
        socket = null
    }
    catch (ex) {
        for (var i = 1; i <= proNum; i++) {
            log(ex, i)
        }
    }
}

function log(msg, num) {
    if (msg[0] === '*' && msg[1] === 's'
        && msg[2] === 'e' && msg[3] === 'l'
        && msg[4] === 'f' && msg[5] === '*') {
        var folder_name = ""
        var file_name = ""
        var state = 0
        var j = 0

        while (1) {
            if (j === msg.length) {
                break
            }
            else if (msg[j] === '*') {
                state++
            }
            else if (msg[j] === '/') {
                state++
            }
            else if (state === 2) {
                folder_name += msg[j]
            }
            else if (state === 3) {
                file_name += msg[j]
            }
            j++
        }

        staff_image(folder_name, file_name, num)
        return
    }
    else if (msg[0] === '*' && msg[1] === 'l'
        && msg[2] === 'o' && msg[3] === 'g'
        && msg[4] === '*') {
        var folder_name2 = ""
        var file_name2 = ""
        var state2 = 0
        var j2 = 0

        while (1) {
            if (j2 === msg.length) {
                break
            }
            else if (msg[j2] === '*') {
                state2++
            }
            else if (msg[j2] === '/') {
                state2++
            }
            else if (state2 === 2) {
                folder_name2 += msg[j2]
            }
            else if (state2 === 3) {
                file_name2 += msg[j2]
            }
            j2++
        }

        user_Image(folder_name2, file_name2, num)
        return
    }

    msg = replace_em(msg)
    var IP_str = ''
    var client_msg = ""
    if (msg.indexOf('连接成功/IP=') >= 0) {
        for (var i = 0; i < msg.length; i++) {
            if (msg[i] === '=') {
                IP_str = ""
            }
            else {
                IP_str += msg[i]
            }
        }
        $("#chat" + num).empty()
        user_IP[num] = IP_str
        msg = "连接成功"
        isConnect[num] = 1
        push_evaluation_num[num] = 0
    }
    else if (msg.indexOf('*转接成功！*') >= 0) {
        user_IP[num] = "0.0.0.0"
        msg = "转接成功！"
        isConnect[num] = 0
    }

    if (msg === '*成功断开聊天连接*') {
        isConnect[num] = 0
        user_IP[num] = "0.0.0.0"
    }
    if (msg.indexOf('Logout*') >= 0) {
        isConnect[num] = 0
        user_IP[num] = "0.0.0.0"
    }

    date = new Date()
    var new_time = get_time(date.getHours()) + ":" + get_time(date.getMinutes())
    var htmlData = '<li class ="msg_box">'
    if (new_time !== time[num]) {
        time[num] = new_time
        htmlData = htmlData
            + '<p class = "time"><span>' + time[num] + '</span></p>'
    }
    if (msg !== '') {
        var htmlData = htmlData
            + '<div class="msg">'
            + '<p>'
            + user_IP[num]
            + '</p>'
            + '<img class = "avartar" width ="30" height = "30" src = "static/images/chat.png">'
            + '<div class="text">'
            + msg
            + '</div>'
            + '</div>'
            + '</li>'
        client_msg = client_msg
            + msg
        $("#chat" + num).append(htmlData)
        $("#chat_content" + num).empty()
        $("#chat_content" + num).append(client_msg)
        $("#chat_time" + num).empty()
        $("#chat_time" + num).append(time[num])
        $("#chat_messagebox" + num).scrollTop($("#chat_messagebox" + num)[0].scrollHeight + 20)
        $("#chat_messagebox" + num).val('')
    }
}

function get_time(time) {
    time = time.toString()
    if (time.length === 1)
        return '0' + time
    return time
}

function log_user_message(msg, num) {
    msg = replace_em(msg)
    date = new Date()
    var new_time = get_time(date.getHours()) + ":" + get_time(date.getMinutes())
    var htmlData = '<li class ="msg_box">'
    var staff_msg = ""
    if (new_time !== time[num]) {
        time[num] = new_time
        htmlData = htmlData
            + '<p class = "time"><span>' + time[num] + '</span></p>'
    }
    if (msg !== '') {
        var htmlData = htmlData
            + '<div class ="user_msg">'
            + '<img class = "avartar" width ="30" height = "30" src =' + ph_url + '>'
            + '<div class="text">'
            + msg
            + '</div>'
            + '</div>'
            + '</div>'
            + '</li>'
        staff_msg = staff_msg + msg
        $("#chat" + num).append(htmlData)
        $("#chat_content" + num).empty()
        $("#chat_content" + num).append(staff_msg)
        $("#chat_time" + num).empty()
        $("#chat_time" + num).append(time[num])
        $("#chat_messagebox" + num).scrollTop($("#chat_messagebox" + num)[0].scrollHeight + 20)
        $("#chat_messagebox" + num).val('')
    }
}

document.onkeydown = function (event) {
    var e = event || window.event || arguments.callee.caller.arguments[0]
    if (event.ctrlKey && (e && e.keyCode === 13)) {
        send(usernum)

    }
}

function clientPressed(num) {
    usernum = num
    document.getElementById("InputMessage" + usernum).focus()
    for (var i = 1; i <= proNum; i++) {
        if (parseInt(num) !== i) {
            document.getElementById("chatting_box" + String(i)).style.display = 'none'
        }
        else {
            document.getElementById("chatting_box" + String(i)).style.display = 'block'
        }
    }
    for (var i = 1; i <= proNum; i++) {
        if (parseInt(num) !== i) {
            document.getElementById("client" + String(i)).style.backgroundColor = 'white'
        }
        else {
            document.getElementById("client" + String(i)).style.backgroundColor = '#d6edfd'
        }
    }
}

function check_process_num(processNum) {
    proNum = processNum

}

function user_Image(folder_name, file_name, num) {
    date = new Date()
    var new_time = get_time(date.getHours()) + ":" + get_time(date.getMinutes())
    var htmlData = '<li class ="msg_box">'
        + '<p class = "time"><span>' + new_time + '</span></p>'
        + '<div class="msg">'
        + '<img class = "avartar" width ="30" height = "30" src = "static/images/chat.png">'
        + '<img src = ' + 'static/user_image/' + folder_name + '/' + file_name + ' height = "200">'
        + '</div>'
        + '</li>'
    $("#chat" + num).append(htmlData)
    $("#chat_messagebox" + num).scrollTop($("#chat_messagebox" + num)[0].scrollHeight + 20)
    $("#chat_messagebox" + num).val('')
}

function staff_image(folder_name, file_name, num) {
    date = new Date()
    var new_time = get_time(date.getHours()) + ":" + get_time(date.getMinutes())
    var htmlData = '<li class ="msg_box">'
        + '<p class = "time"><span>' + new_time + '</span></p>'
        + '<div class="user_msg">'
        + '<img class = "avartar" width ="30" height = "30" src = "static/images/chat.png">'
        + '<img src = ' + 'static/staff_image/' + folder_name + '/' + file_name + ' height = "200">'
        + '</div>'
        + '</li>'
    $("#chat" + num).append(htmlData)
    $("#chat_messagebox" + num).scrollTop($("#chat_messagebox" + num)[0].scrollHeight + 20)
    $("#chat_messagebox" + num).val('')
}

function addClient(photo_url) {
    ph_url = photo_url
    for (var i = 1; i <= proNum; i++) {
        push_evaluation_num[i] = 0
        var client_chat = '<div class = "chatting_box" id=chatting_box' + String(i) + '>' +
            '<div class="staff_head">' +
            '<span class="sc_title_text">'+
            '<span class="sc_visitor_code" title="v18962464">'+
            '用户 ' + String(i) + ''+
            '</span>'+
            '</span>'+
            '<span class="staff_operation">' +
            '<a href="javascript:;" onclick="change_staff(' + String(i) + ')" id="defriend" class="sc_con">' +
            '<i class="b_icon"></i>'+
            '<span>转接</span>'+
            '</a>' +
            '<a href="javascript:;" onclick="defriend(' + String(i) + ')" id="defriend" class="sc_over">' +
            '<i class="b_icon"></i>' +
            '<span>结束会话</span>' +
            '</a>'+
            '</span>' +
            '</div>' +
            '<div class="chat_messagebox" id=chat_messagebox' + String(i) + '>' +
            '<ul id=chat' + String(i) + '>' +
            '</ul>' +
            '</div>' +
            '<div class="staff_send">' +
            '<div class="staff_icon" id=staff_icon' + String(i) + '>' +
            '<ul>' +
            '<li id=emotion' + String(i) + ' class="emotion" title="表情" style="display: inline-block;float:left">' +
            '</li>' +
            '<li href="javascript:;" class="file" title="未选择文件" style="display: inline-block;" onclick="new_send_image(' + String(i) + ')">' +
            '</li>' +
            '<li id=evaluate' + String(i) + ' class="evaluate" title="推送评价" style="display: inline-block;float:left" onclick="push_evaluation(push_evaluation_msg, usernum)">' +
            '</li>' +
            '</ul>' +
            '</div>' +
            '<textarea type="text" placeholder="按Ctrl+Enter键发送消息" class="form_control" id=InputMessage' + String(i) + ' style="resize: none;font-size:15px"cols="50" rows="7"></textarea>' +
            '<button class="btn btn-primary" id="send_button" onclick="send(' + String(i) + ')" type="submit">' +
            'Send' +
            '</button>' +
            '</div>' +
            '</div>'
        $(".staff_box_c").append(client_chat)
        var clientName = "client" + String(i)
        var clientBox =
            '<div class ="client" id=client' + String(i) + ' onclick=clientPressed(' + String(i) + ')>' +
            '<div class="content_text">' +
            '<div class ="chat_staff_time" id = chat_time' + String(i) + '>'+
            '</div>'+
            '<div class="clientIP">'+
            clientName +
            '</div>' +
            '<div class ="chat_staff_message" id = chat_content' + String(i) + '>' +
            '</div>' +
            '</div> ' +
            '</div> '
        $(".select-client").append(clientBox)
    }

}

function new_send_image(num) {
    socket.send('{' + String(num) + '}' + '*create image data*')
    window.open("image_send", "image_send", "width = 250px, height = 202px")
}

function quick_message(process_num, message) {
    process_num = Number(process_num)
    for (i = 1; i <= process_num; i++) {
        if ($('#chatting_box' + String(i)).css('display') === 'block') {
            $('#InputMessage' + String(i)).append(message)
        }
    }
}

function defriend(num) {
    try {
        user_IP[num] = "0.0.0.0"
        socket.send('{' + String(num) + '}' + '*defriend*' + String(num))
    } catch (ex) {
        log(ex, num)
    }
}

function change_staff(num) {
    try {
        socket.send('{' + String(num) + '}' + '对方正在尝试转接给别的客服人员')
        socket.send('{' + String(num) + '}' + '*change_staff*' + String(num))
    } catch (ex) {
        log(ex, num)
    }
}

function push_evaluation(msg, num) {
    if (isConnect[num] === 1) {
        if (push_evaluation_num[num] === 0) {
            var evaluation_msg = "推送评价成功"
        }
        if (push_evaluation_num[num] === 1) {
            var evaluation_msg = "你已经推送过评价"
            var push_msg
            push_msg = '{' + num + '}'
            push_msg += evaluation_msg
            var json_data = check_num(push_msg)
            log_user_message(json_data.msg, usernum)

        }
        if (push_evaluation_num[num] === 0) {
            var push_msg
            push_msg = '{' + num + '}'
            push_msg += evaluation_msg
            try {
                socket.send(msg)
            } catch (ex) {
                for (var i = 1; i <= proNum; i++) {
                    log(ex, i)
                }
            }
            var json_data = check_num(push_msg)
            log_user_message(json_data.msg, usernum)
            push_evaluation_num[num] = 1
        }
    }
}
