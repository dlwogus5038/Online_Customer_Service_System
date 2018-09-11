var company_code = '000000'
var ifm = document.createElement('iframe')
document.body.appendChild(ifm)
ifm.src = "/toolbar_chat_" + company_code
ifm.className = "suspend"
ifm.style.width = "40px"
ifm.style.height = "198px"
ifm.frameBorder = "0"
ifm.scrolling = "no"
ifm.style.right = "0"
ifm.style.bottom = "60%"
ifm.style.position = "fixed"
ifm.overflow = "hidden"


function open_chat(code) {
    var check = 0
    var m_keywords = new Array('iPhone','iPod','Android','SAMSUNG','LG')
    for(var mobile in m_keywords){
        if(navigator.userAgent.match(m_keywords[mobile])!== null) {
            check = 1
            window.open("/m_chat_" + code)
            break
         }
    }
    if(check === 0){
        window.open("/chat_" + code, "chat", "width = 650px, height = 502px， resizable=No")
    }
}

function ifm_chat(code) {
    var check = 0
    var m_keywords = new Array('iPhone','iPod','Android','SAMSUNG','LG')
    for(var mobile in m_keywords){
        if(navigator.userAgent.match(m_keywords[mobile])!== null) {
            check = 1
            alert("在移动端，不能使用嵌入型")
            break
         }
    }
    if(check === 0){
        var ifm2 = document.createElement('iframe')
        parent.document.body.appendChild(ifm2)
        ifm2.src = "/chat_" + code
        ifm2.frameBorder = "0"
        ifm2.id = "ifm_chat"
        ifm2.width = "650px"
        ifm2.height = "500px"
        ifm2.scrolling = "no"
        ifm2.style.right = "0px"
        ifm2.style.bottom = "0px"
        ifm2.style.position = "fixed"
    }
}

$(document).ready(function () {

    $(".suspend").mouseover(function () {
        $(this).stop()
        $(this).animate({width: 160}, 400)
    })

    $(".suspend").mouseout(function () {
        $(this).stop()
        $(this).animate({width: 40}, 400)
    })
})

function init_data() {
    var sc = document.getElementsByTagName('script')
    var params
    for (var i = 0; i < sc.length; i++) {
        params = sc[i].src
        if (params !== "") {
            var params = sc[i].src.split('?')[0]
            if (params.substring(params.length - 17) === "chat_interface.js") {
                var params_arr = sc[i].src.split('?')[1]
            }
        }
    }
    company_code = params_arr.split('=')[1]
    ifm.src = "/toolbar_chat_" + company_code
}