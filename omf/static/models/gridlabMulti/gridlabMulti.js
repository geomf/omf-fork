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
    function editFeeder(e) {
        studyUser = $(e).siblings("select").val().split(/[_]+/)[0];
        studyName = $(e).siblings("select").val().split(/[_]+/)[1];
        $(e).attr("href", "/feeder/" + studyUser + "/" + studyName)
            .attr("target", "_blank");
    }

    $(document).ready(function () {
        $('.content .add-feeder').click(function () {
            var n = $('.feederList').length + 1;
            if (5 < n) {
                alert('Please do not add more than 5 feeders.');
                return false;
            }
            var feeder_html = $('<div class="feederList shortInput"><label for="feeder' + n + '">Feeder <span class="feeder-number" >' + n + ' </span></label><a class="remove-feeder postRun preRun stopped" href="#" style="display:inline" title="Remove feeder">&#8854;</a><select id="feederName' + n + '" name="feederName' + n + '" style="width:90%"><option disabled><strong>Personal Feeders</strong></option>{% for feeder in datastoreNames["feeders"] %}<option value="{{ datastoreNames["currentUser"] + "___" + feeder }}">{{ feeder }}</option>{% endfor %}<option disabled><strong>Public Feeders</strong></option>{% for pFeeder in datastoreNames["publicFeeders"] %}<option value="{{ "public___" + pFeeder }}">{{ pFeeder }}</option>{% endfor %}</select><a class="edit-feeder postRun preRun stopped" onclick="editFeeder(this);" target="_blank" style="display: inline;" title="Edit feeder"> &#9997;</a></div>');
            feeder_html.hide();
            $('.content .feederList:last').after(feeder_html);
            feeder_html.fadeIn('slow');
            return false;
        });
        $('#recalculateCostBenefit').on('click', recalculateCostBenefit);
        $('.content').on('click', '.remove-feeder', function () {
            $(this).parent().css('background-color', '#FF6C6C');
            $(this).parent().fadeOut("slow", function () {
                $(this).remove();
                $('.feeder-number').each(function (index) {
                    $(this).text(index + 1 + " ");
                });
                $('select[id*="feederName"]').each(function (index) {
                    $(this).attr("id", "feederName" + index + 1);
                });
            });
            return false;
        });
    });
    $(document).ready(function () {
        $(".toggle").click(function () {
            $(this).parent().next().toggle(500)
        })
    });


    /*
     * Global setting of Highcharts
     */

    // Clean up the non-ISO date strings we get.
    function dateOb(inStr) {
        return Date.parse(inStr.replace(/-/g, "/"))
    }

    pointStart = dateOb(allOutputData.timeStamps[0]);
    pointInterval = dateOb(allOutputData.timeStamps[1]) - pointStart;
    var timeStamps = allOutputData.timeStamps.map(function (a) {
        return new Date(a)
    });
    studyList = [];
    for (key in allInputData) {
        if (key.substring(0, 10) === "feederName") {
            feederKey = "feeder_" + allInputData[key].split("___")[1]
            if (allOutputData[feederKey] != undefined) {
                studyList.push(feederKey)
            }
        }
    }

    /*
     * This is a HighChart display for power consumption
     */
    for (index in studyList) {
        study = studyList[index]
        $("<div/>").appendTo("#powerConsumptionReport")
            .attr("class", "studyContainer")
            .attr("id", study)
            .append("<div class='studyTitleBox'><p class='studyTitle'>" + study.substring(7) + "</p></div>")
        // Create div of power timeseries appending to powerConsumption
        $("<div/>").appendTo("#powerConsumptionReport .studyContainer:last")
            .attr("id", "powerTimeSeries_" + study.replace(/ /g, ""));
        // power series data

        var chartOptions = new LineChartModule.C3LineChartOptions(
            980, 150,
            "#powerTimeSeries_" + study.replace(/ /g, ""),
            {
                x: 'x',
                json: {
                    x: timeStamps,
                    data1: allOutputData[study].Consumption.Power,
                    data2: allOutputData[study].Consumption.Losses,
                    data3: allOutputData[study].Consumption.DG

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
        chartOptions.options.axis.y.label = {
            text: 'Power (W)',
            position: 'outer-middle'
        };
        c3.generate(chartOptions.options);
    }

    /*
     * This is a HighChart display for energy balance
     */
    var tLossesSeries = [];
    var tLoadsSeries = [];
    var tDGSeries = [];
    var cateList = [];
    for (index in studyList) {
        study = studyList[index];
        // energy balance bar
        var tPower = eval(allOutputData[study].Consumption.Power.join("+"));
        var tLosses = eval(allOutputData[study].Consumption.Losses.join("+"));
        var tDG = eval(allOutputData[study].Consumption.DG.join("+"));
        var tLoads = tPower + tDG - tLosses;
        tLossesSeries.push(tLosses);
        tLoadsSeries.push(tLoads);
        tDGSeries.push(tDG);
        cateList.push(study.substring(7))
    }
    var barChartOptions = new BarChartModule.C3BarChartOptions(
        980, 250,
        "#energyBalanceReport",
        {
            json: {
                data1: tLossesSeries,
                data2: tLoadsSeries,
                data3: tDGSeries

            },
            colors: {
                data1: "orangered",
                data2: "darkorange",
                data3: "seagreen"
            },
            names: {
                data1: "Losses",
                data2: "Loads",
                data3: "DG"
            },
            type: 'bar',
            types: {
                data3: 'scatter'
            },
            groups: [
                ['data1', 'data2', 'data3']
            ],
            order: 'asc'
        },
        cateList);
    barChartOptions.options.axis.y.label = {
        text: 'Energy (Wh)',
        position: 'outer-middle'
    };
    c3.generate(barChartOptions.options);

    /*
     * This is a HighChart for triplex meter voltages
     */
    for (index in studyList) {
        study = studyList[index];
        // Create div for triplex meter voltage chart appending to powerConsumption
        $("<div/>").appendTo("#triplexMeterVoltageReport")
            .attr("class", "studyContainer")
            .attr("id", study)
            .append("<div class='studyTitleBox'><p class='studyTitle'>" + study.substring(7) + "</p></div>")
        $("<div/>").appendTo("#triplexMeterVoltageReport .studyContainer:last")
            .attr("id", "triplexMeterVoltageChart_" + study.replace(/ /g, ""));

        var chartOptions = new LineChartModule.C3LineChartOptions(
            980, 150,
            "#triplexMeterVoltageChart_" + study.replace(/ /g, ""),
            {
                x: 'x',
                json: {
                    x: timeStamps,
                    data1: allOutputData[study].allMeterVoltages.Min,
                    data2: allOutputData[study].allMeterVoltages.Mean,
                    data3: allOutputData[study].allMeterVoltages.Max

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
    }

    /*
     * HighChart template for power time series, data renders at recalculateCostBenefit func.
     */
    var series = {};
    series['x'] = timeStamps;
    for (key in allOutputData) {
        if (key.substring(0, 6) == "feeder") {
            series[key] = [];
        }
    }
    var chartOptions = new LineChartModule.C3LineChartOptions(
        480, 200,
        "#monetizedPowerTimeSeries",
        {
            x: 'x',
            json: series
        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Capacity Cost ($)',
        position: 'outer-middle'
    };
    monCapCostGraph = c3.generate(chartOptions.options);

    /*
     * HighChart template for energy balance, data renders at recalculateCostBenefit func.
     */

    var chartOptions = new LineChartModule.C3LineChartOptions(
        480, 200,
        "#monetizedEnergyBalance",
        {
            x: 'x',
            json: series
        }
    );
    chartOptions.options.axis.y.tick = {};
    chartOptions.options.axis.y.label = {
        text: 'Energy Cost ($)',
        position: 'outer-middle'
    };
    monEnergyCostGraph = c3.generate(chartOptions.options);
    /*
     * HighChart template for culumative savings, data renders at recalculateCostBenefit func.
     */
    intervalMap = {"minutes": 60, "hours": 3600, "days": 86400}
    yearPercentage = intervalMap[allInputData.simLengthUnits] * (allOutputData.timeStamps.length) / (365 * 34 * 60 * 60.0)
    delete series['x'];
    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 200,
        "#costGrowthContainer",
        {
            json: series
        }
    );
    chartOptions.options.axis.x = {};
    chartOptions.options.tooltip.format = {
        title: function (d) {
            return d;
        },
        value: function (value, ration, id) {
            return chartOptions.addCommas(value.toFixed(1));
        }
    };
    chartOptions.options.axis.y.label = {
        text: 'Cumulative Savings ($)',
        position: 'outer-middle'
    };
    costGrowthGraph = c3.generate(chartOptions.options);


    gebi('distrEnergyRate').value = (allInputData.distrEnergyRate || 0.08)
    gebi('distrCapacityRate').value = (allInputData.distrCapacityRate || 15)
    firstTime = true
    for (index in studyList) {
        study = studyList[index]
        if (undefined != study) {
            // Add table row:
            table = gebi('additionalMetricsTable')
            newRow = table.insertRow()
            newRow.id = 'row' + study
            if (firstTime) {
                checked = 'checked';
                cap = '0';
                om = '0';
                firstTime = false
            } else {
                checked = '';
                cap = (allInputData['equipAndInstallCost'] || 30000);
                om = (allInputData['opAndMaintCost'] || 1000)
            }
            newRow.innerHTML = '<td class="studyName">' + study + '</td>' +
                '<td><input type="radio" name="baseline" class="baseline" ' + checked + '/></td>' +
                '<td><input class="capCost" value="' + cap + '"/></td>' +
                '<td><input class="omCost" value="' + om + '"/></td>' +
                '<td class="capacityCost">calcMe</td>' +
                '<td class="energyCost">calcMe</td>' +
                '<td class="y1save">calcMe</td>' +
                '<td class="annualSave">calcMe</td>' +
                '<td class="payback">calcMe</td>'
        }
    }


    // render data for monetization charts
    recalculateCostBenefit();
    function recalculateCostBenefit() {
        /*
         * Calculate the cost of power and energy
         */
        console.log("aaa")
        energyRate = (parseFloat(gebi('distrEnergyRate').value) || 0.08)
        capRate = (parseFloat(gebi('distrCapacityRate').value) || 15)
        // Update everything not depending on baseline diff.
        for (index in studyList) {
            study = studyList[index]
            if (undefined != study) {
                // Update the capacity graph.

                function maxAvg(arr) {
                    max = arrMax(arr.filter(function (n) {
                        return n != undefined
                    }));
                    len = arr.length;
                    return arr.map(function (x) {
                        return max / len
                    })
                }

                powerAgged = monthAgg(allOutputData.timeStamps, allOutputData[study].Consumption.Power, maxAvg)
                monthlyPower = powerAgged.map(function (x) {
                    return round(x * capRate / 1000, 4)
                })
                monthlyPower.unshift(study);
                timeStamps.unshift('x');
                monCapCostGraph.load({columns: [timeStamps, monthlyPower]});
                monthlyPower.shift();

                // Update the energy graph.

                function avg(arr) {
                    total = arrSum(arr.filter(function (n) {
                        return n != undefined
                    }));
                    len = arr.length;
                    return arr.map(function (x) {
                        return total / len
                    })
                }

                energyAgged = monthAgg(allOutputData.timeStamps, allOutputData[study].Consumption.Power, avg)
                monthlyEnergy = energyAgged.map(function (x) {
                    return round(x * energyRate / 1000, 4)
                });
                monthlyEnergy.unshift(study);
                monEnergyCostGraph.load({columns: [timeStamps, monthlyEnergy]});
                monthlyEnergy.shift();
                timeStamps.shift();
                // update the table:
                thisRow = gebi('row' + study)
                thisRow.querySelector('.capacityCost').innerHTML = round(arrSum(monthlyPower), 4)
                thisRow.querySelector('.energyCost').innerHTML = round(arrSum(monthlyEnergy), 4)
            }
        }
        // Calculate baseline.
        baseRow = gebi('additionalMetricsTable').querySelector('[checked]').parentElement.parentElement
        baseAnnual = parseFloat(baseRow.querySelector('.omCost').value) + parseFloat(baseRow.querySelector('.capacityCost').innerHTML) / yearPercentage + parseFloat(baseRow.querySelector('.energyCost').innerHTML) / yearPercentage
        baseCost = baseAnnual + parseFloat(baseRow.querySelector('.capCost').value)
        baseRow.querySelector('.y1save').innerHTML = '0'
        baseRow.querySelector('.annualSave').innerHTML = '0'
        baseRow.querySelector('.payback').innerHTML = '0'
        // Update things that depend on the baseline diff.
        for (index in studyList) {
            study = studyList[index]
            if (undefined != study) {
                // Update the table:
                thisRow = gebi('row' + study)
                annualCost = parseFloat(thisRow.querySelector('.omCost').value) + parseFloat(thisRow.querySelector('.capacityCost').innerHTML) / yearPercentage + parseFloat(thisRow.querySelector('.energyCost').innerHTML) / yearPercentage
                y1cost = annualCost + parseFloat(thisRow.querySelector('.capCost').value)
                y1save = baseCost - y1cost
                thisRow.querySelector('.y1save').innerHTML = round(y1save, 4)
                annualSave = baseAnnual - annualCost
                thisRow.querySelector('.annualSave').innerHTML = round(annualSave, 4)
                thisRow.querySelector('.payback').innerHTML = round(Math.abs(y1save / annualSave), 2)
                // update the costBen graph.
                costSeries = []
                for (i = 0; i < 30; i++) {
                    costSeries.push(round(baseCost - y1cost + i * (baseAnnual - annualCost), 4))
                }
                costSeries.unshift(study);
                costGrowthGraph.load({columns: [costSeries]});
                costSeries.shift();
            }
        }
    }

    function monthAgg(stamps, power, func) {
        // Aggregate a month's worth of power.
        combo = zip([stamps, power])
        grouped = partition(combo, function (x, y) {
            return x[0].substring(5, 7) == y[0].substring(5, 7)
        })
        function dropStamp(pairArr) {
            return pairArr.map(function (x) {
                return x[1]
            })
        }

        noStamps = grouped.map(dropStamp)
        applied = noStamps.map(func)
        return flatten1(applied)
    }


    var width = 500,
        height = 350;
    var projection = d3.geo.albersUsa().scale(600).translate([width / 2, height / 2]);
    var path = d3.geo.path()
        .projection(projection);
    var svg = d3.select("#mapHere").append("svg")
        .attr("width", width)
        .attr("height", height);
    var group = svg.append("g");
    group.attr("transorm", "scale(.2, .2)");
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
            .style('stroke-width', 1);
    });
    d3.json("/static/city_locations.json", function (new_us_places) {
        climate = allInputData.climateName
        var ST_NAME = climate.split("-");
        ST = ST_NAME[0]
        NAME = ST_NAME[1].replace("_", " ")
        var my_coords = projection(new_us_places[ST][NAME]);
        var r = 5;
        circle = svg.append("circle")
            .attr("cx", my_coords[0])
            .attr("cy", my_coords[1])
            .attr("r", 5)
            .attr("class", "HighlightCircle");
        circle.append("svg:title").text(climate);
    })


    pieData = [];
    for (index in studyList) {
        size = parseInt(allOutputData[studyList[index]]["stdout"].split("\n")[3].split(/[ ]+/)[2])
        pieData.push([studyList[index], size])
    }
    var chartOptions = new LineChartModule.C3ChartOptions(
        300, 300,
        "#comparisonPieChart",
        {
            columns: pieData,
            type: 'pie'
        }
    );
    chartOptions.options.pie = {
        label: {
            show: false
        }
    };
    chartOptions.options.tooltip.format = {
        value: function (value, ratio, id) {
            return chartOptions.addCommas(value.toFixed(1));
        }
    };
    chartOptions.options.legend = {
        hide: true
    };
    c3.generate(chartOptions.options);

    /*
     * HighChart for climate data.
     */
    var exampleData = [];
    for (var i = 0; i < timeStamps.length; i++) {
        exampleData.push(0);
    }
    for (index in studyList) {
        study = studyList[index];
        $("<div/>").appendTo("#climateReport")
            .attr("id", "climateChartDiv");
        var chartOptions = new LineChartModule.C3LineChartOptions(
            980, 250,
            "#climateChartDiv",
            {
                x: 'x',
                json: {
                    x: timeStamps,
                    data1: allOutputData.climate["Wind Speed (m/s)"] == null
                        ? exampleData : allOutputData.climate["Wind Speed (m/s)"],
                    data2: allOutputData.climate["Direct Insolation (W/m^2)"] == null
                        ? exampleData : allOutputData.climate["Direct Insolation (W/m^2)"],
                    data3: allOutputData.climate["Temperature (F)"] == null
                        ? exampleData : allOutputData.climate["Temperature (F)"],
                    data4: allOutputData.climate["Snow Depth (in)"] == null
                        ? exampleData : allOutputData.climate["Snow Depth (in)"]

                },
                hide: [],
                colors: {
                    data1: "darkgray",
                    data2: "darkgray",
                    data3: "gainsboro",
                    data4: "gainsboro"
                },
                names: {
                    data1: "Wind Speed (m/s)",
                    data2: "Direct Insolation (W/m^2)",
                    data3: "Temperature (F)",
                    data4: "Snow Depth (in)"
                }

            }
        );

        chartOptions.options.axis.y.tick = {};
        chartOptions.options.axis.y.label = {
            text: 'Climate Units',
            position: 'outer-middle'
        };
        c3.generate(chartOptions.options);
    }


    /*
     * display stdout
     */
    for (index in studyList) {
        study = studyList[index]
        $("<pre/>").appendTo("#runtimeStatsReport")
            .attr("id", "stdout_" + study)
            .attr("class", "stdoutBlock")
            .attr("style", "margin:5 0 5 0")
        gebi("stdout_" + study).innerHTML = study + "\n" + allOutputData[study].stdout
    }
    // TODO: add stderr if some failed feeders exist.


    /* Highlight failed feeders */
    $(window).bind("load", function () {
        if (allOutputData != null) {
            $("select[id*='feederName']").each(function () {
                study = $(this).val().split("___")[1]
                name = "feeder_" + study
                if (allOutputData[name] == undefined) {
                    // highlight feeders in input form
                    $(this).parent("div").css("background-color", "#FFF000");
                    // render stderr to runtimeStatsReport
                    $("<pre/>").appendTo("#runtimeStatsReport")
                        .attr("id", "stderr_" + study)
                        .attr("class", "stdoutBlock")
                    gebi("stderr_" + study).innerHTML = study + "\n\n" + allOutputData["failures"][name]["stderr"]
                }
            })
        }
    })
})(LineChart, BarChart);