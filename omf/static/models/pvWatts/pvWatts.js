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

(function (LineChartModule) {
    // Clean up the non-ISO date strings we get.
    function dateOb(inStr) {
        return Date.parse(inStr.replace(/-/g, "/"))
    }

    pointStart = dateOb(allOutputData.timeStamps[0]);
    pointInterval = dateOb(allOutputData.timeStamps[1]) - pointStart;
    var timeStamps = allOutputData.timeStamps.map(function (a) {
        return new Date(a)
    });
    // Handle special case for inverter sizing:
    if (allInputData.inverterSize == 0) {
        chartInverter = allInputData.systemSize
    }
    else {
        chartInverter = allInputData.inverterSize
    }
    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 250,
        "#powerTimeSeries",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.Consumption.Power

            },
            colors: {
                data1: "red"
            },
            names: {
                data1: "Power Generated"
            }

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Power (W-AC)',
        position: 'outer-middle'
    };
    chartOptions.options.legend = {
        show: false
    };
    chartOptions.options.grid.y = {
        show: true,
        lines: [
            {
                text: 'Panels Nameplate',
                value: parseFloat(allInputData.systemSize) * 1000,
                class: 'nameplate',
                position: 'end'
            },
            {
                text: 'Inverter Nameplate',
                value: parseFloat(chartInverter) * 1000,
                class: 'nameplate',
                position: 'start'
            }
        ]
    };
    c3.generate(chartOptions.options);


    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 250,
        "#irradianceChartDiv",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.climate["Plane of Array Irradiance (W/m^2)"],
                data2: allOutputData.climate["Beam Normal Irradiance (W/m^2)"],
                data3: allOutputData.climate["Diffuse Irradiance (W/m^2)"]
            },
            colors: {
                data1: "yellow",
                data2: "gold",
                data3: "lemonchiffon"
            },
            names: {
                data1: "Plane of Array Irradiance (W/m^2)",
                data2: "Beam Normal Irradiance (W/m^2)",
                data3: "Diffuse Irradiance (W/m^2)"
            }

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Climate Units',
        position: 'outer-middle'
    };
    c3.generate(chartOptions.options);

    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 250,
        "#climateChartDiv",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.climate["Ambient Temperature (F)"],
                data2: allOutputData.climate["Cell Temperature (F)"],
                data3: allOutputData.climate["Wind Speed (m/s)"]
            },
            colors: {
                data1: "dimgray",
                data2: "gainsboro",
                data3: "darkgray"
            },
            names: {
                data1: "Ambient Temperature (F)",
                data2: "Cell Temperature (F)",
                data3: "Wind Speed (m/s)"
            }

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Climate Units',
        position: 'outer-middle'
    };
    c3.generate(chartOptions.options);

})(LineChart);