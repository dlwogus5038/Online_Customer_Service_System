$.extend({
    message: function (options) {
        var defaults = {
            message: ' 操作成功',
            time: '2000',
            type: 'success',
            showClose: false,
            autoClose: true,
            onClose: function () {
            }
        }

        if (typeof options === 'string') {
            defaults.message = options
        }
        if (typeof options === 'object') {
            defaults = $.extend({}, defaults, options)
        }

        var templateClose = defaults.showClose ? '<a class="show_message_close">×</a>' : ''
        var template = '<div class="show_message messageFadeInDown">' +
            '<i class=" show_message_icon show_message_' + defaults.type + '"></i>' +
            templateClose +
            '<div class="show_message_tip">' + defaults.message + '</div>' +
            '</div>'
        var $body = $('body')
        var $message = $(template)
        var timer
        var closeFn, removeFn

        closeFn = function () {
            $message.addClass('messageFadeOutUp')
            $message.one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function () {
                removeFn()
            })
        }

        removeFn = function () {
            $message.remove()
            defaults.onClose(defaults)
            clearTimeout(timer)
        }

        $('.show_message').remove()
        $body.append($message)

        $message.css({
            'margin-left': '-' + $message.width() / 2 + 'px'
        })

        $message.one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function () {
            $message.removeClass('messageFadeInDown')
        })

        $body.on('click', '.show_message_close', function (e) {
            closeFn()
        })

        if (defaults.autoClose) {
            timer = setTimeout(function () {
                closeFn()
            }, defaults.time)
        }
    }
})

function print_message(message_type, message_content) {
    $.message({
        message: message_content,
        type: message_type
    })
}