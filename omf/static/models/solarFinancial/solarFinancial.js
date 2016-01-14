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
    function insertMetric(tableId, name, vector) {
        // Add a vector to a table as a row.
        table = gebi(tableId)
        newRow = table.insertRow()
        newRow.insertCell().innerHTML = name
        for (i = 0; i < vector.length; i++) {
            cell = newRow.insertCell()
            cell.innerHTML = delimitNumbers(vector[i].toFixed(0))
        }
    }

    // Clean up the non-ISO date strings we get.
    function dateOb(inStr) {
        return Date.parse(inStr.replace(/-/g, "/"))
    }

    pointStart = dateOb(allOutputData.timeStamps[0]);
    pointInterval = dateOb(allOutputData.timeStamps[1]) - pointStart;
    var timeStamps = allOutputData.timeStamps.map(function (a) {
        return new Date(a)
    });
    gebi("projName").innerHTML = allInputData.modelName
    gebi("climSource").innerHTML = allInputData.climateName
    gebi("sysSize").innerHTML = parseFloat(allInputData.systemSize)
    gebi("invSize").innerHTML = parseFloat(allInputData.inverterSize)
    gebi("perClip").innerHTML = (parseFloat(allOutputData.percentClipped).toFixed(1)) + "%"
    gebi("purchCost").innerHTML = "$" + delimitNumbers(parseFloat(allInputData.installCost))
    gebi("costperKWP").innerHTML = (parseFloat(allInputData.installCost) / parseFloat(allInputData.systemSize)).toFixed(0)
    gebi("1yearKWH").innerHTML = delimitNumbers((parseFloat(allOutputData.oneYearGenerationWh) / 1000).toFixed(0))
    gebi("1yearSales").innerHTML = "$" + delimitNumbers(allOutputData.lifeGenerationDollars[0].toFixed(0))
    gebi("1yearOM").innerHTML = "$" + delimitNumbers(parseFloat(allInputData.omCost).toFixed(0))
    gebi("lifeKWH").innerHTML = delimitNumbers((parseFloat(allOutputData.lifeGenerationWh) / 1000).toFixed(0))
    gebi("lifeOM").innerHTML = "$" + delimitNumbers((parseFloat(allInputData.omCost) * parseFloat(allInputData.lifeSpan)).toFixed(0))
    gebi("lifeEnergy").innerHTML = "$" + delimitNumbers(allOutputData.lifeEnergySales.toFixed(0))
    gebi("ROI").innerHTML = parseFloat(allOutputData.ROI).toFixed(3)
    gebi("NPV").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.NPV.toFixed(0)))
    gebi("NPV").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.NPV.toFixed(0)))
    gebi("IRR").innerHTML = parseFloat(allOutputData.IRR)


    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 250,
        "#powerTimeSeries",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.powerOutputAc,
                data2: allOutputData.InvClipped
            },
            colors: {
                data1: "red",
                data2: "purple"
            },
            names: {
                data1: "Power Generated",
                data2: "Power After Inverter Clipping"
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
                text: 'DC Nameplate',
                value: parseFloat(allInputData.systemSize) * 1000,
                class: 'nameplate',
                position: 'end'
            },
            {
                text: 'AC Nameplate',
                value: parseFloat(allInputData.inverterSize) * 1000,
                class: 'nameplate',
                position: 'start'
            }
        ]
    };
    chartOptions.options.tooltip = {
        show: false
    };
    c3.generate(chartOptions.options);

    var barCategory = allOutputData.monthlyGeneration.map(function (a) {
        return a[0];
    });
    var barValues = allOutputData.monthlyGeneration.map(function (a) {
        return a[1];
    });
    var barChartOptions = new BarChartModule.C3BarChartOptions(
        980, 250,
        "#monthlyPerformanceDiv",
        {
            json: {
                data1: barValues

            },
            colors: {
                data1: "orange"
            },
            names: {
                data1: "Energy Generated"
            },
            type: 'bar'
        },
        barCategory);
    barChartOptions.options.axis.y.label = {
        text: 'Energy (Wh-AC)',
        position: 'outer-middle'
    };
    barChartOptions.options.legend = {
        show: false
    };
    c3.generate(barChartOptions.options);

    createHeatMap(allOutputData.seasonalPerformance);

    var barChartOptions = new BarChartModule.C3BarChartOptions(
        980, 250,
        "#cashFlowChartDiv",
        {
            json: {
                data1: allOutputData.lifeGenerationDollars,
                data2: allOutputData.lifeOmCosts,
                data3: allOutputData.lifePurchaseCosts,
                data4: allOutputData.netCashFlow,
                data5: allOutputData.cumCashFlow
            },
            names: {
                data1: "Energy Sales",
                data2: "Op. and Maint. Costs",
                data3: "Purchase Costs",
                data4: "Net",
                data5: "Cumulative"
            },
            type: 'bar',
            types: {
                data4: 'line',
                data5: 'line'
            }
        },
        []);
    barChartOptions.options.bar = {
        width: 5
    };
    barChartOptions.options.point = {
        r: 3
    };
    barChartOptions.options.axis.x = {
        label: {
            text: "ROI:" + allOutputData.ROI.toFixed(3) + ", NPV:$" + delimitNumbers(allOutputData.NPV.toFixed(0)) + ", IRR:" + allOutputData.IRR
        }
    };
    barChartOptions.options.axis.y.label = {
        text: 'Income ($)',
        position: 'outer-middle'
    };
    c3.generate(barChartOptions.options);

    d3.select('#cashFlowChartDiv svg').append('text')
        .attr('x', 500)
        .attr('y', 247)
        .attr('text-anchor', 'middle')
        .style('font-size', '1em').style('fill', 'grey')
        .text('Year After Installation');

    table = gebi("monthlySummaryTable")
    newRow = table.insertRow()
    newRow.insertCell().innerHTML = "Month"
    for (i = 0; i < allOutputData.monthlyGeneration.map(function (x) {
        return x[1]
    }).length; i++) {
        cell = newRow.insertCell()
        cell.innerHTML = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][i]
    }
    insertMetric("monthlySummaryTable", "Single Residential PV System Generation (kWh)", allOutputData.monthlyGeneration.map(function (x) {
        return x[1] / 1000
    }))

    insertMetric("annualSummaryTable", "Year", Array.apply(null, {length: parseFloat(allInputData.lifeSpan)}).map(Number.call, Number))
    insertMetric("annualSummaryTable", "Generation Income", allOutputData.lifeGenerationDollars)
    insertMetric("annualSummaryTable", "Purchase Costs", allOutputData.lifePurchaseCosts)
    insertMetric("annualSummaryTable", "Op. and Maint. Costs", allOutputData.lifeOmCosts)
    insertMetric("annualSummaryTable", "Net Income", allOutputData.netCashFlow)
    insertMetric("annualSummaryTable", "Cumulative Income", allOutputData.cumCashFlow)

    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 300,
        "#irradianceChartDiv",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.climate["Plane of Array Irradiance (W/m^2)"],
                data2: allOutputData.climate["Global Horizontal Radiation (W/m^2)"]
            },
            colors: {
                data1: "gold",
                data2: "goldenrod"
            },
            names: {
                data1: "Plane of Array Irradiance",
                data2: "Global Horizontal Radiation"
            }

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Climate Units',
        position: 'outer-middle'
    };
    chartOptions.options.tooltip = {
        show: false
    }
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
    chartOptions.options.tooltip = {
        show: false
    }
    c3.generate(chartOptions.options);

    width = 1000, height = 350
    projection = d3.geo.albersUsa().scale(600).translate([width / 2, height / 2])
    path = d3.geo.path()
        .projection(projection)
    svg = d3.select("#mapHere").append("svg")
        .attr("width", width)
        .attr("height", height)
    group = svg.append("g")
    group.attr("transorm", "scale(.2, .2)")
    d3.json('/static/state_boundaries.json', function (collection) {
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

    function createHeatMap(data) {
        var margin = {top: 100, right: 0, bottom: 100, left: 60},
            width = 960 - margin.left - margin.right,
            height = 450 - margin.top - margin.bottom,
            times = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
            gridSize = Math.floor(width / times.length),
            gridHeight = gridSize * 2 / 3,
            legendElementWidth = gridSize / 12,
            days = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            heatmapHeight = gridHeight * days.length,
            heatmapWidth = gridSize * times.length;
        var colors = ["#FFFFFF", "#F8E4E4", "#F8E1E1", "#F7DFDF", "#F7DDDD", "#F6DBDB", "#F6D8D8", "#F5D6D6", "#F5D4D4", "#F4D2D2", "#F4CFCF", "#F3CDCD", "#F3CBCB", "#F2C9C9", "#F2C6C6", "#F1C4C4", "#F1C2C2", "#F0C0C0", "#F0BDBD", "#EFBBBB", "#EFB9B9", "#EEB7B7", "#EEB4B4", "#EDB2B2", "#EDB0B0", "#ECAEAE", "#EBABAB", "#EBA9A9", "#EAA7A7", "#EAA5A5", "#E9A2A2", "#E9A0A0", "#E89E9E", "#E89C9C", "#E79999", "#E79797", "#E69595", "#E69393", "#E59090", "#E58E8E", "#E48C8C", "#E48A8A", "#E38787", "#E38585", "#E28383", "#E28181", "#E17E7E", "#E17C7C", "#E07A7A", "#E07878", "#DF7575", "#DF7373", "#DE7171", "#DE6F6F", "#DD6C6C", "#DD6A6A", "#DC6868", "#DC6666", "#DB6363", "#DB6161", "#DA5F5F", "#DA5D5D", "#D95A5A", "#D85858", "#D85656", "#D75454", "#D75151", "#D64F4F", "#D64D4D", "#D54B4B", "#D54848", "#D44646", "#D44444", "#D34242", "#D33F3F", "#D23D3D", "#D23B3B", "#D13939", "#D13636", "#D03434", "#D03232", "#CF3030", "#CF2D2D", "#CE2B2B", "#CE2929", "#CD2727", "#CD2424", "#CC2222", "#CC2020", "#CB1E1E", "#CB1B1B", "#CA1919", "#CA1717", "#C91515", "#C91212", "#C81010", "#C80E0E", "#C70C0C", "#C70A0A"];
        var svg = d3.select("#seasonalPerformanceDiv").append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        data = data.map(
            function (d) {
                return {
                    day: +d[1],
                    hour: +d[0],
                    value: +d[2]
                };
            });

        var colorScale = d3.scale.quantile()
            .domain([0, d3.max(data, function (d) {
                return d.value;
            })])
            .range(colors);

        textStyle = {
            font: '10px sans-serif'
        };

        function drawAxis() {
            var axisStyle = {
                'fill': 'none',
                'stroke': '#000',
                'shape-rendering': 'crispEdges'
            };
            svg.selectAll(".dayLabel")
                .data(days)
                .enter().append("text")
                .text(function (d) {
                    return d;
                })
                .attr("x", 0)
                .attr("y", function (d, i) {
                    return i * (gridHeight);
                })
                .style("text-anchor", "end")
                .style(textStyle)
                .attr("transform", "translate(-6," + gridHeight / 1.5 + ")");
            times.push("")
            var x = d3.scale.ordinal()
                .domain(times)
                .rangePoints([0, heatmapWidth]);
            times.pop()
            var xAxis = d3.svg.axis()
                .scale(x)
                .orient("bottom");

            svg.append("g")
                .attr("transform", "translate(0," + heatmapHeight + ")")
                .style(axisStyle)
                .call(xAxis)
                .selectAll(".tick text")
                .style("text-anchor", "start")
                .style(textStyle)
                .attr("x", 15)
                .attr("y", 6);

            var x = d3.scale.identity()
                .domain([0, width]);

            var xAxis = d3.svg.axis()
                .scale(x)
                .ticks(0)
                .orient("top");
            svg.append("g")
                .attr("transform", "translate(0," + (-1) + ")")
                .attr("class", "x axis")
                .style(axisStyle)
                .call(xAxis);
        }


        function drawLabels() {
            svg.append("text")
                .attr("text-anchor", "end")
                .attr("x", width)
                .attr("y", -6)
                .style(textStyle)
                .text("Does not adjust for Daylight Savings Time");


            svg.append("text")
                .attr("transform", "translate(" + legendElementWidth + ", 0)")
                .attr("y", -80)
                .style({
                    'font-family': '"Lucida Grande", "Lucida Sans Unicode", Arial, Helvetica, sans-serif',
                    'font-size': '12px',
                    'font-weight': 'bold',
                    'fill': 'gray'
                })
                .text("Energy (Wh-AC)");

            svg.append("text")
                .attr("x", width / 2)
                .attr("y", heatmapHeight + 40)
                .style(textStyle)
                .text("Hour of the Day");
        }

        function drawLegend() {
            var legend = svg.selectAll(".legend")
                .data([0].concat(colorScale.quantiles()), function (d) {
                    return d;
                });

            legend.enter().append("g")
                .attr("class", "legend");

            legend.append("rect")
                .attr("x", function (d, i) {
                    return legendElementWidth * i;
                })
                .attr("y", -70)
                .attr("width", legendElementWidth)
                .attr("height", gridSize / 2)
                .style("fill", function (d, i) {
                    return colors[i];
                });

            legend.append("text")
                .text(function (d) {
                    if (d % 25000 < 700)
                        return Math.floor(d / 1000) + "k";
                })
                .attr("x", function (d, i) {
                    return legendElementWidth * i;
                })
                .attr("y", -70 + gridSize);

            legend.exit().remove();
        }


        var heatmapChart = function (tsvFile) {


            var cards = svg.selectAll(".hour")
                .data(tsvFile, function (d) {
                    return d.day + ':' + d.hour;
                });

            cards.append("title");
            var valueScale = d3.scale.linear()
                .domain([0, d3.max(tsvFile, function (d) {
                    return d.value;
                })])
                .range([0, legendElementWidth * colors.length]);  // Set margins for x specific
            cards.enter().append("rect")
                .attr("x", function (d) {
                    return (d.hour) * gridSize;
                })
                .attr("y", function (d) {
                    return (d.day) * (gridHeight);
                })
                .attr("width", gridSize)
                .attr("height", gridHeight)
                .style("fill", colors[0])
                .on('mouseover', function (d, i) {
                    d3.select(this).style({
                        fill: "black"
                    });

                    svg.append("rect").attr({
                        id: "line-" + d.hour + "-" + d.day + "-" + i,
                        x: function () {
                            return valueScale(d.value);
                        },
                        y: function () {
                            return -75;
                        }
                    }).attr("width", 1)
                        .attr("height", gridHeight)
                        .style({
                            fill: "black"
                        });
                })
                .on('mouseout', function (d, i) {
                    d3.select(this).style({
                        fill: colorScale(d.value)
                    });
                    d3.select("#line-" + d.hour + "-" + d.day + "-" + i).remove();
                });

            cards.transition().duration(1000)
                .style("fill", function (d) {
                    return colorScale(d.value);
                });

            cards.select("title").text(function (d) {
                return d.value;
            });

            cards.exit().remove();
        };
        drawAxis();
        drawLabels();
        drawLegend();
        heatmapChart(data);
    }

})(LineChart, BarChart);