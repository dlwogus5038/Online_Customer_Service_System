var date_arr = []
var data = []
var fn

function make_record(_date, _num) {
    date_arr.push(_date)
    data.push(_num)
}


function draw_chatting_graph() {
    var x_coor = []
    var y_coor = []
    var start_date = document.getElementById('startDate').value
    var end_date = document.getElementById('endDate').value
    start_date = new Date(start_date.replace(/-/g, "/"))
    end_date = new Date(end_date.replace(/-/g, "/"))
    for (index in date_arr) {
        cur_date = date_arr[index]
        cur_date = new Date(cur_date.replace(/-/g, "/"))
        if (cur_date >= start_date && cur_date <= end_date) {
            x_coor.push(date_arr[index])
            y_coor.push(data[index])
        }
    }
    fn('统计数据', 'graph', x_coor, y_coor, '日期', '数量')
}

function draw_todays_graph() {
    fn('今日统计数据', 'graph', date_arr, data, '时间', '数量')
}

function draw_area_graph() {
    var y_coor = []
    var area_coor = []
    var start_date = document.getElementById('startDate').value
    var end_date = document.getElementById('endDate').value
    start_date = new Date(start_date.replace(/-/g, "/"))
    end_date = new Date(end_date.replace(/-/g, "/"))
    for (index in date_arr) {
        cur_date = date_arr[index]
        cur_date = new Date(cur_date.replace(/-/g, "/"))
        if (cur_date >= start_date && cur_date <= end_date) {
            area_coor.push(data[index])
        }
    }

    area_coor.sort()
    for (var i = 0; i < area_coor.length;) {
        var count = 0
        var area_datum = {}
        for (var j = i; j < area_coor.length; j++) {
            if (area_coor[i] === area_coor[j]) {
                count++
            }
        }
        area_datum['name'] = area_coor[i]
        area_datum['y'] = count
        y_coor.push(area_datum)
        i += count
    }

    fn('graph', y_coor, '区域', '数量')
}


function init_graph() {
    var charts = []
    var colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    Highcharts.setOptions({
        colors: colors,
        global: {
            useUTC: false
        }
    })

    function make_chart(title, divId, x_coor, y_coor, x_title, y_title) {
        var chart = new Highcharts.Chart({
            chart: {
                renderTo: divId,
                type: 'spline'
            },
            title: {
                text: ''
            },
            xAxis: {
                title: {
                    enabled: false
                },
                categories: x_coor
            },
            yAxis: {
                title: {
                    enabled: false
                }
            },
            plotOptions: {
                column: {
                    pointPadding: 0.45,
                    borderWidth: 0
                }
            },
            legend: {},
            credits: {
                enabled: false
            },
            tooltip: {
                formatter: function () {
                    return '<span style="color:' + this.series.color + ';font-weight:bold;">' + x_title + ':</span><b>' + this.x +
                        '</b><br/><span style="color:' + this.series.color + ';font-weight:bold;">' + y_title + ':</span><b>' + this.y + '</b>'
                },
                crosshairs: true
            },
            series: [{
                name: title,
                data: y_coor
            }]
        })
        return chart
    }

    fn = make_chart
}

function init_area_graph() {
    var charts = []
    var colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    Highcharts.setOptions({
        colors: colors,
        global: {
            useUTC: false
        }
    })

    function make_area_chart(divId, y_coor, x_title, y_title) {
        var chart = new Highcharts.Chart({
            chart: {
                renderTo: divId,
                type: 'column'
            },
            title: {
                text: ''
            },
            xAxis: {
                title: {
                    enabled: false
                },
                type: 'category'
            },
            yAxis: {
                title: {
                    enabled: false,
                }
            },

            plotOptions: {
                series: {
                    borderWidth: 0,
                    dataLabels: {
                        enabled: true,
                        format: '{point.y}'
                    }
                },
                column: {
                    pointPadding: 0.47,
                    borderWidth: 0
                }
            },
            legend: {},
            credits: {
                enabled: false
            },
            tooltip: {
                headerFormat: '',
                pointFormat: '<span style="color:{point.color}; font-weight:bold;"> 区域:</span><b>{point.name}</b><br>' +
                '<span style="color:{point.color}; font-weight:bold;">数量:</span><b>{point.y}</b><br>'
            },
            series: [{
                name: "区域",
                colorByPoint: true,
                data: y_coor
            }]
        })
        return chart
    }

    fn = make_area_chart
}