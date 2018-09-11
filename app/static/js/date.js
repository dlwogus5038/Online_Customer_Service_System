(function ($) {
    $.setStartTime = function () {
        $('.startDate').datepicker({
            dateFormat: "yy-mm-dd",
            maxDate: "+d",
            onClose: function (dateText, inst) {
                if (dateText > $("input[name=endDate]").val()) {
                    alert("开始日期不能大于结束日期！")
                    $("input[name=startDate]")[0].value = $("input[name=endDate]").val()
                }
            }
        })
    }
    $.setEndTime = function () {
        $(".endDate").datepicker({
            dateFormat: "yy-mm-dd",
            maxDate: "+d",
            defaultDate: new Date(),
            onClose: function (dateText, inst) {
                if (dateText < $("input[name=startDate]").val()) {
                    alert("结束日期不能小于开始日期！")
                    $("input[name=endDate]")[0].value = $("input[name=startDate]").val()
                }
            }
        })
    }
    $.date = function () {
        $('.date').datepicker(
            $.extend({showMonthAfterYear: true}, $.datepicker.regional['zh-CN'],
                {
                    'showAnim': '', 'dateFormat': 'yy-mm-dd', 'changeMonth': 'true', 'changeYear': 'true',
                    'showButtonPanel': 'true'
                }
            ))
    }
    $.datepickerjQ = function () {
        $(".ui-datepicker-time").on("click", function () {
            $(".ui-datepicker-css").css("display", "block")
        })
        $(".ui-kydtype li").on("click", function () {
            $(".ui-kydtype li").removeClass("on").filter($(this)).addClass("on")
        })
        $(".ui-datepicker-quick input").on("click", function () {
            var thisAlt = $(this).attr("alt")
            var dateList = timeConfig(thisAlt)
            $(".ui-datepicker-time").val(dateList)
            $(".ui-datepicker-css").css("display", "none")
            $("#ui-datepicker-div").css("display", "none")
//            getAppCondtion()
        })
        $(".ui-close-date").on("click", function () {
            $(".ui-datepicker-css").css("display", "none")
            $("#ui-datepicker-div").css("display", "none")
            //inst.dpDiv.css({"display":"none"})
        })
        $(".startDate").on("click", function () {
            $(".endDate").attr("disabled", false)
        })

    }

})(jQuery)

function get_date(cur_date) {
    cur_date = String(cur_date)
    if (cur_date.length < 2) {
        cur_date = '0' + cur_date
    }
    return cur_date
}

$(function () {
    $.setStartTime()
    $.setEndTime()
    $.datepickerjQ()

    var nowDate = new Date()
    timeStr = nowDate.getFullYear() + '-' + get_date(nowDate.getMonth() + 1) + '-' + get_date(nowDate.getDate())
    nowDate.setDate(nowDate.getDate() + parseInt(-1))
    var endDateStr = nowDate.getFullYear() + '-' + (nowDate.getMonth() + 1) + '-' + nowDate.getDate()
    $(".ui-datepicker-time").attr("value", endDateStr + "—" + timeStr)
    //$("#startDate").attr("value",endDateStr)
    $("#endDate").attr("value", timeStr)
})


function timeConfig(time) {
    //快捷菜单的控制
    var nowDate = new Date()
    timeStr = '一' + nowDate.getFullYear() + '-' + (nowDate.getMonth() + 1) + '-' + nowDate.getDate()
    nowDate.setDate(nowDate.getDate() + parseInt(time))
    var endDateStr = nowDate.getFullYear() + '-' + (nowDate.getMonth() + 1) + '-' + nowDate.getDate()
    if (Number(time) === -1) {
        endDateStr += '一' + endDateStr
    } else {
        endDateStr += timeStr
    }
    return endDateStr
}

