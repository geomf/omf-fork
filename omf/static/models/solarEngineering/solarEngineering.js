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

(function (LineChartModule, BarChartModule) {
    var timeStamps = allOutputData.timeStamps.map(function (a) {
        return new Date(a)
    });

    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 150,
        "#powerTimeSeries",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.Consumption.Power,
                data2: allOutputData.Consumption.Losses,
                data3: allOutputData.Consumption.DG

            },
            hide: ['data2', 'data3'],
            colors: {
                data1: "red",
                data2: "orangered",
                data3: "seagreen"
            },
            names: {
                data1: "Substation Powerflow",
                data2: "Technical Losses",
                data3: "DG Power"
            }

        }
    );
    chartOptions.options.axis.y.label= {
            text: 'Power (W)',
            position: 'outer-middle'

    };
    c3.generate(chartOptions.options);


    function dateOb(inStr) {
        return Date.parse(inStr.replace(/-/g, "/"))
    }


    function editFeeder(e) {
        studyUser = $(e).siblings("select").val().split(/[_]+/)[0]
        studyName = $(e).siblings("select").val().split(/[_]+/)[1]
        $(e).attr("href", "/feeder/" + studyUser + "/" + studyName)
            .attr("target", "_blank");
    }

    // Code to make the toggles work:
    $(document).ready(function () {
        $(".toggle").click(function () {
            $(this).parent().next().toggle(500)
        })
        $("#feederChangeButton").click(function () {editFeeder(this)});
    })


    function arrSum(arr) {
        myVal = eval(arr.join("+"))
        if (typeof myVal == "undefined") {
            return 0
        } else {
            return myVal
        }
    }

    tPower = eval(allOutputData.Consumption.Power.join("+"))
    tLosses = eval(allOutputData.Consumption.Losses.join("+"))
    tDG = eval(allOutputData.Consumption.DG.join("+"))
    tLoads = tPower + tDG - tLosses
    dgExported = []
    fromGrid = []
    for (i = 0; i < allOutputData.Consumption.Power.length; i++) {
        curVal = allOutputData.Consumption.Power[i]
        if (curVal < 0) {
            dgExported.push(curVal)
        } else {
            fromGrid.push(curVal)
        }
    }
    tDGExported = arrSum(dgExported)
    tFromGrid = arrSum(fromGrid)
    tDGDirect = tLoads + tLosses - tFromGrid

    var chartOptions = new BarChartModule.C3BarChartOptions(
        980, 250,
        "#newEnergyBalanceReport",
        {
            json: {
                data1: [0, tLosses],
                data2: [0, tLoads],
                data3: tDG,
                data4: [tFromGrid, 0],
                data5: [tDGDirect, 0],
                data6: [tDGExported, 0]
            },
            colors: {
                data1: "orangered",
                data2: "darkorange",
                data3: "seagreen",
                data4: "red",
                data5: "RoyalBlue",
                data6: "LightSeaGreen"
            },
            names: {
                data1: "Losses",
                data2: "Loads",
                data3: "DG",
                data4: "FromGrid",
                data5: "DGDirect",
                data6: "DG Exported"
            },
            hide: ['data3'],
            groups: [
                ['data1', 'data2', 'data3'],
                ['data4', 'data5', 'data6']
            ]
        },
        ["Source", "Destination"]
    );
    chartOptions.options.axis.rotated = true;
    chartOptions.options.axis.y.label = {
            text: 'Energy (Wh)',
            position: 'outer-center'
        }
    c3.generate(chartOptions.options);
    var regulatorStamps = [timeStamps[0].getTime()];
    for(var i = 0; i < timeStamps.length;i++) {
        regulatorStamps.push(regulatorStamps[i] + (3 * 3600 * 100));
    }

    var regNamesArray = []
    for (var key in allOutputData) {
        if (key.indexOf('Regulator') === 0) {
            regName = "allOutputData.".concat(key);
            regNamesArray.push(regName)
        }
    }
    for (var i in regNamesArray) {

        reg = regNamesArray[i]
        $("<div/>").appendTo("#newRegulatorReport")
            .attr("class", "regContainer")
            .attr("id", reg)
        $("<div/>").appendTo("#newRegulatorReport")
            .attr("id", "regulatorSeries_" + reg.replace('.', '_'))

        phaseValue = eval(reg.concat(".RegPhases"))
        var series = {
            x: 'x',
            json: {
                x: regulatorStamps
            },
            colors: {},
            names: {}
        };
        if (phaseValue.indexOf('A') != -1) {
            series.json.data1 = eval(regNamesArray[i].concat(".RegTapA"));
            series.colors.data1 = "RoyalBlue";
            series.names.data1 = "A";
        }
        if (phaseValue.indexOf('B') != -1) {
            series.json.data2 = eval(regNamesArray[i].concat(".RegTapB"));
            series.colors.data2 = "Red";
            series.names.data2 = "B";
        }
        if (phaseValue.indexOf('C') != -1) {
            series.json.data3 = eval(regNamesArray[i].concat(".RegTapC"));
            series.colors.data3 = "Green";
            series.names.data3 = "C";
        }
        var chartOptions = new LineChartModule.C3LineChartOptions(
            980, 150,
            "#regulatorSeries_" + reg.replace('.', '_'),
            series
        );
        chartOptions.options.axis.y.label = {
                text: 'Tap position',
                position: 'outer-middle'
        };
        //title = reg.substr(14)
        chartOptions.options.point = {
            r: 3
        };
        c3.generate(chartOptions.options);
    }

    var capNamesArray = []
    for (var key in allOutputData) {
        if (key.indexOf('Capacitor') === 0) {
            capName = "allOutputData.".concat(key);
            capNamesArray.push(capName)
        }
    }
    for (var i in capNamesArray) {
        cap = capNamesArray[i]
        //$("<div/>").appendTo("#newCapbankReport")
        //	.attr("id", "capacitorSeries")
        $("<div/>").appendTo("#newCapbankReport")
            .attr("class", "capContainer")
            .attr("id", cap)

        $("<div/>").appendTo("#newCapbankReport")
            .attr("id", "capacitorSeries_" + cap.replace('.', '_'))

        phaseValue = eval(cap.concat(".CapPhases"))

        var series = {
            x: 'x',
            json: {
                x: regulatorStamps
            },
            type: 'bar',
            groups: [[]
            ],
            colors: {},
            names: {}
        };
        if (phaseValue.indexOf('A') != -1) {
            series.json.data1 = eval(capNamesArray[i].concat(".Cap1A"));
            series.colors.data1 = "RoyalBlue";
            series.names.data1 = "A";
            series.groups[0].push('data1');
        }
        if (phaseValue.indexOf('B') != -1) {
            series.json.data2 = eval(capNamesArray[i].concat(".Cap1B"));
            series.colors.data2 = "Red";
            series.names.data2 = "B";
            series.groups[0].push('data2');
        }
        if (phaseValue.indexOf('C') != -1) {
            series.json.data3 = eval(capNamesArray[i].concat(".Cap1C"));
            series.colors.data3 = "Green";
            series.names.data3 = "C";
            series.groups[0].push('data3');
        }

        //3 * 3600 * 100

        var chartOptions = new BarChartModule.C3LineChartOptions(
            980, 150,
            "#capacitorSeries_" + cap.replace('.', '_'),
            series
        );
        chartOptions.options.axis.y.label = {
                text: '1 = Active',
                position: 'outer-middle'
        };
        //title = cap.substr(14)
        c3.generate(chartOptions.options);
    }


    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 200,
        "#triplexMeterVoltageChart",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.allMeterVoltages.Min,
                data2: allOutputData.allMeterVoltages.Mean,
                data3: allOutputData.allMeterVoltages.Max

            },
            hide: [],
            colors: {
                data1: "LightBlue",
                data2: "blue",
                data3: "LightBlue"
            },
            names: {
                data1: "Min",
                data2: "Mean",
                data3: "Max"
            }

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Volts',
        position: 'outer-middle'
    };
    chartOptions.options.grid.y = {
        show: true,
        lines: [
            {value: 114, class: 'gridLines'},
            {value: 126, class: 'gridLines'}
        ]
    };
    c3.generate(chartOptions.options);

    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 300,
        "#irradianceChartDiv",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.climate['Global Horizontal (W/sm)']
            },
            colors: {
                data1: "gold"
            },
            names: {
                data1: "Global Horizontal"
            }

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Irradiance ( W / m^2 )',
        position: 'outer-middle'
    };
    c3.generate(chartOptions.options);

    var exampleData = [];
    for (var i = 0; i < timeStamps.length; i++) {
        exampleData.push(0);
    }

    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 250,
        "#climateChartDiv",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.climate["Wind Speed (m/s)"] == null
                    ? exampleData : allOutputData.climate["Wind Speed (m/s)"],
                data2: allOutputData.climate["Temperature (F)"] == null
                    ? exampleData : allOutputData.climate["Temperature (F)"],
                data3: allOutputData.climate["Snow Depth (in)"] == null
                    ? exampleData : allOutputData.climate["Snow Depth (in)"]
            },
            colors: {
                data1: "darkgray",
                data2: "gainsboro",
                data3: "gainsboro"
            },
            names: {
                data1: "Wind Speed (m/s)",
                data2: "Temperature (F)",
                data3: "Snow Depth (in)"
            }

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Climate Units',
        position: 'outer-middle'
    };
    c3.generate(chartOptions.options);

    width = 495, height = 340
    projection = d3.geo.albersUsa().scale(600).translate([width / 2, height / 2])
    path = d3.geo.path()
        .projection(projection)
    svg = d3.select("#mapHere").append("svg")
        .attr("width", width)
        .attr("height", height)
    group = svg.append("g")
    group.attr("transorm", "scale(.2, .2)")
    d3.json("/static/state_boundaries.json", function (collection) {
        group.selectAll('path')
            .data(collection.features)
            .enter().append('path')
            .attr('d', d3.geo.path().projection(projection))
            .attr('id', function (d) {
                return d.properties.name.replace(/\s+/g, '')
            })
            .style('fill', 'gray')
            .style('stroke', 'white')
            .style('stroke-width', 1)
    })
    d3.json("/static/city_locations.json", function (new_us_places) {
        climate = allInputData.climateName
        ST_NAME = climate.split("-")
        ST = ST_NAME[0]
        NAME = ST_NAME[1].replace("_", " ")
        my_coords = projection(new_us_places[ST][NAME])
        r = 5
        circle = svg.append("circle")
            .attr("cx", my_coords[0])
            .attr("cy", my_coords[1])
            .attr("r", 5)
            .attr("class", "HighlightCircle")
        circle.append("svg:title").text(climate)
    })

    gebi("stdout").innerHTML = allOutputData.stdout

})(LineChart, BarChart);