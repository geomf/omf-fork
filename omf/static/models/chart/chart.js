/*
 Open Modeling Framework (OMF) Software for simulating power systems behavior
 Copyright (c) 2015, Intel Corporation.

 This program is free software; you can redistribute it and/or modify it
 under the terms and conditions of the GNU General Public License,
 version 2, as published by the Free Software Foundation.

 This program is distributed in the hope it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
 more details.
 */
var Chart = (function () {
    var module = {};

    module.C3ChartOptions = function (width, height, bindTo, series) {
        var self = this;
        this.addCommas = function (nStr) {
            nStr += '';
            x = nStr.split('.');
            x1 = x[0];
            x2 = x.length > 1 ? '.' + x[1] : '';
            var rgx = /(\d+)(\d{3})/;
            while (rgx.test(x1)) {
                x1 = x1.replace(rgx, '$1' + ',' + '$2');
            }
            return x1 + x2;
        };
        var max = Number.MIN_VALUE;
        for (var element in series.json) {
            if (element != 'x') {
                var tmp = d3.max(series.json[element]);
                if (max < tmp) {
                    max = tmp;
                }
            }
        }
        var even = true;

        function tickFormat(d) {
            if (even) {
                even = false;
                var value = d.toFixed(2);
                if (max / 1000000 > 1) {
                    return value / 1000000 + "M"
                } else if (max / 1000 > 1) {
                    return value / 1000 + "k"
                } else {
                    return value;
                }
            }
            even = true;
        }

        this.options = {
            bindto: bindTo,
            data: series,
            tooltip: {
                grouped: false,
                format: {
                    value: function (value, ration, id) {
                        return self.addCommas(value.toFixed(1));
                    }
                }
            },
            point: {
                show: false
            },
            legend: {
                position: 'inset',
                inset: {
                    anchor: 'top-left',
                    x: 10,
                    y: 0,
                    step: 1
                }
            },
            zoom: {
                enabled: true
            },
            grid: {
                y: {
                    show: true
                }
            },
            size: {
                width: width,
                height: height
            },
            axis: {
                x: {},
                y: {
                    padding: {
                        top: 60,
                        bottom: 20
                    },
                    tick: {
                        outer: false,
                        format: function (d) {
                            return tickFormat(d)
                        }
                    }
                }
            }
        };
    };

    return module;
})();