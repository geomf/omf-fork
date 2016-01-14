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
var LineChart = (function (module) {

    module.C3LineChartOptions = function (width, height, bindTo, series) {
        module.C3ChartOptions.call(this, width, height, bindTo, series);
        var self = this;
        self.options.tooltip.format.title = function (d) {
            var formatter = d3.time.format("%A, %b %d, %H:%M");
            return formatter(d);
        };

        self.options.axis.x = {
            type: 'timeseries',
            tick: {
                count: 15,
                outer: false,
                format: "%d. %b"
            }
        };
    };
    module.C3LineChartOptions.prototype = Object.create(module.C3ChartOptions.prototype);

    return module;
})(Chart);