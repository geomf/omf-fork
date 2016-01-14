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

    // Alert the user if some of the inputs were invalid.
    arrayOfMaxes = allOutputData.LevelizedCosts.filter(function (x) {
        return x[1] == 200
    })
    if (arrayOfMaxes.length > 0) {
        alert("Warning: a levelized cost was higher than the loan algorithms could calculate. It is being displayed as $200/MWh.")
    }
    if (parseFloat(allInputData.landAmount) < allOutputData.minLandSize) {
        alert("Warning: the minimum amount of land required for this system based on its latitude is " + allOutputData.minLandSize + " acres, but you have specified " + allInputData.landAmount + " acres.")
    }
    if (parseFloat(allInputData.systemDcSize) > 2.0 * allInputData.systemSize) {
        alert("Warning: the inverter appears to be poorly sized to the Array size.  Please review your inputs. Array size is:" + allInputData.systemDcSize + "kW and your inverter is only " + allInputData.systemSize + "kW. Most inverts will not tolerate more than 2x nameplate rating")
    }
    // Function to add a vector to a table as a row.
    function insertMetric(tableId, name, vector) {
        table = gebi(tableId)
        newRow = table.insertRow()
        newRow.insertCell().innerHTML = name
        for (i = 0; i < vector.length; i++) {
            cell = newRow.insertCell()
            cell.innerHTML = delimitNumbers(vector[i].toFixed(0))
        }
    }


    var objectsList = [];
    var barFilteredData = allOutputData.LevelizedCosts.filter(function (a) {
        if (a instanceof Array) {
            return a[1];
        } else {
            objectsList.push(a);
        }
    });
    var barCategory = barFilteredData.map(function (a) {
        return a[0];
    });
    var barValues = barFilteredData.map(function (a) {
        return a[1];
    });
    for (var i = 0; i < objectsList.length; i++) {
        barValues.push(objectsList[i].y);
        //barChartOptions.options.data.colors[i] = objectsList[i].color;
        barCategory.push(objectsList[i].name);
    }
    var barChartOptions = new BarChartModule.C3BarChartOptions(
        480, 300,
        "#levelizedCostDiv",
        {
            json: {
                data1: barValues
            },
            color: function (color, d) {
                if (d.hasOwnProperty('value')) {
                    var result = objectsList.filter(function (element) {
                        return d.value == element.y;
                    });
                    if (result.length === 1) {
                        return result[0].color;
                    }
                }
                return color;
            },
            labels: {
                format: function (v, id, i, j) {
                    return v.toFixed(2);
                }
            },
            colors: {
                data1: "green"
            },
            names: {
                data1: "Levelized Cost ($/MWh)"
            },
            type: 'bar'
        },
        barCategory);
    barChartOptions.options.axis.y = {
        padding: {
            top: 80,
            bottom: 20
        },
        tick: {
            outer: false,
            format: function (d) {
                if (d % 25 === 0) {
                    return d
                }
            }
        },
        label: {
            text: 'Levelized Cost ($/MWh)',
            position: 'outer-middle'
        }
    };
    barChartOptions.options.tooltip.format.value = function (value, ration, id) {
        return barChartOptions.addCommas(value.toFixed(2));
    };

    barChartOptions.options.legend = {
        show: false
    };
    barChartOptions.options.bar = {
        width: 25
    };
    c3.generate(barChartOptions.options);

    if (typeof(allInputData.stderr) !== 'undefined') {
        gebi('errorText').innerHTML = '\nFULL ERROR TEXT FOLLOWS\n' + allInputData.stderr
    }
    gebi("levelCostDirect").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.levelCostDirect).toFixed(2))
    gebi("costPanelDirect").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.costPanelDirect).toFixed(2))
    gebi("cost10WPanelDirect").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.cost10WPanelDirect).toFixed(2))
    gebi("levelCostNCREB").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.levelCostNCREB).toFixed(2))
    gebi("costPanelNCREB").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.costPanelNCREB).toFixed(2))
    gebi("cost10WPanelNCREB").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.cost10WPanelNCREB).toFixed(2))
    gebi("levelCostTaxLease").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.levelCostTaxLease).toFixed(2))
    gebi("costPanelTaxLease").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.costPanelTaxLease).toFixed(2))
    gebi("cost10WPanelTaxLease").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.cost10WPanelTaxLease).toFixed(2))
    gebi("levelCostTaxEquity").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.levelCostTaxEquity).toFixed(2))
    gebi("costPanelTaxEquity").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.costPanelTaxEquity).toFixed(2))
    gebi("cost10WPanelTaxEquity").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.cost10WPanelTaxEquity).toFixed(2))
    gebi("levelCostPPA").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.levelCostPPA).toFixed(2))

    var pieChartSum = 0;
    allOutputData.costsPieChart.map(function (d) {
        pieChartSum += d[1];
        return;
    });
    var chartOptions = new LineChartModule.C3ChartOptions(
        490, 300,
        "#breakdownPieChart",
        {
            columns: allOutputData.costsPieChart,
            type: 'pie'
        }
    );
    chartOptions.options.pie = {
        label: {
            show: false
        }
    };
    chartOptions.options.tooltip.format = {
        title: function (value) {
            return "% of Total Cost";
        },
        value: function (value, ratio, id) {
            return (value / pieChartSum * 100).toFixed(1) + "%";
        }
    };
    chartOptions.options.legend = {}
    c3.generate(chartOptions.options);

    pieRef = allOutputData.costsPieChart
    for (var chartRow = 0; chartRow < pieRef.length; chartRow++) {
        thisPerc = pieRef[chartRow][1] / allOutputData.totalCost
        insertMetric("breakdownCostTable", pieRef[chartRow][0], [pieRef[chartRow][1], thisPerc * 100])
    }


    width = 490, height = 280
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

    gebi("totalCost").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.totalCost).toFixed(0))
    gebi("costWdc").innerHTML = "$" + delimitNumbers(parseFloat(allOutputData.costWdc).toFixed(2))
    gebi("capFactor").innerHTML = delimitNumbers(parseFloat(allOutputData.capFactor).toFixed(0)) + "%"
    gebi("perClip").innerHTML = (parseFloat(allOutputData.percentClipped).toFixed(1)) + "%"
    gebi("1yearMWH").innerHTML = delimitNumbers((parseFloat(allOutputData.oneYearGenerationWh) / 1000000).toFixed(0))
    gebi("climSource").innerHTML = allInputData.climateName

})(LineChart, BarChart);