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
var BarChart = (function (module) {

    module.C3BarChartOptions = function (width, height, bindTo, series, categoryList) {
        module.C3ChartOptions.call(this, width, height, bindTo, series);
        var self = this;
        self.options.data.type = 'bar';
        self.options.data.order = 'asc';
        self.options.point = {
            r: 10
        };
        self.options.bar = {
            width: 50
        };
        self.options.axis.x = {
            type: 'category',
            categories: categoryList
        };

        module.C3BarChartOptions.prototype = Object.create(module.C3ChartOptions.prototype);
    };

    return module;
})(Chart);