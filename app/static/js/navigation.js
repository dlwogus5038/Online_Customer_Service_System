$(document).ready(function () {
    $(".nav_show .slide_animate").click(function () {
        if ($(".animate_div").is(":hidden")) {
            if (!$(".animate_div").is(":animated")) {
                $(this).children(".xiala").css({'transform': 'rotate(180deg)'})
                $(".animate_div").animate({
                    height: 'show'
                }, 500)
                    .end().siblings().find(".animate_div").hide(1000)
            }
        } else {
            if (!$(".animate_div").is(":animated")) {
                $(this).children(".xiala").css({'transform': 'rotate(360deg)'})
                $(".animate_div").animate({
                    height: 'hide'
                }, 500)
                    .end().siblings().find(".animate_div").hide(1000)
            }
        }
    })
})
