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

    var barChartOptions = new BarChartModule.C3BarChartOptions(
        980, 200,
        "#scadaReport",
        {
            json: {
                data1: allOutputData["histPeak"],
                data2: allOutputData["histAverage"]
            },
            colors: {
                data1: "darkgrey",
                data2: "grey"
            },
            names: {
                data1: "Energy Generated",
                data2: "Energy Generated"
            },
            type: 'bar'
        },
        allOutputData["monthName"]);
    barChartOptions.options.axis.y.label = {
        text: 'Historical Power Con(KW)',
        position: 'outer-middle'
    };
    barChartOptions.options.bar = {
        width: 10
    };
    c3.generate(barChartOptions.options);

    var barChartOptions = new BarChartModule.C3BarChartOptions(
        980, 200,
        "#spendReport",
        {
            json: {
                data1: allOutputData["energyReductionDollars"],
                data2: allOutputData["lossReductionDollars"],
                data3: allOutputData["peakReductionDollars"]
            },
            colors: {
                data1: "blue",
                data2: "green",
                data3: "red"
            },
            names: {
                data1: "Energy Reduction",
                data2: "Loss Reduction",
                data3: "Peak Reduction"
            },
            type: 'bar'
        },
        allOutputData["monthName"]);
    barChartOptions.options.axis.y.label = {
        text: 'Utility Savings ($)',
        position: 'outer-middle'
    };
    barChartOptions.options.bar = {
        width: 10
    };
    c3.generate(barChartOptions.options);

    paybackYear = null;
    for (i = 0; i <= 30; i++) {
        if (allOutputData["annualSave"][i] >= 0) {
            paybackYear = i;
            break
        }
    }
    paybackLine = [];
    if (paybackYear != null) {
        paybackLine = [{
            "color": "green", // Color value
            "value": paybackYear, // Value of where the line will appear
            "width": 1, // Width of the line
            "label": {"text": "Simple Payback"}
        }]
    }

    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 200,
        "#savingsReport",
        {
            json: {
                data1: allOutputData["annualSave"]
            },
            colors: {
                data1: "blue"
            },
            names: {
                data1: "Cumulative Savings ($)"
            }

        }
    );
    chartOptions.options.axis.x = {};
    var idOfCost = 0;
    chartOptions.options.tooltip.format = {
        title: function (d) {
            idOfCost = d;
            return;
        },
        value: function (value, ration, id) {
            return 'Net return after <b>' + idOfCost + '</b> years is <b>$' + chartOptions.addCommas(value.toFixed(2)) + '</b>';
        }
    };
    chartOptions.options.grid.x = {
        show: true,
        lines: [
            {value: paybackYear, text: "Simple Payback"}
        ]
    };
    chartOptions.options.axis.y.label = {
        text: 'Cumulative Savings ($)',
        position: 'outer-middle'
    };
    chartOptions.options.point = {
        r: 3
    };
    c3.generate(chartOptions.options);

    function insertMetric(tableId, name, vector) {
        // Add a vector to a table as a row.
        table = gebi(tableId)
        newRow = table.insertRow()
        newRow.insertCell().innerHTML = name
        for (i = 0; i < vector.length; i++) {
            cell = newRow.insertCell()
            cell.innerHTML = vector[i]
        }
    }

    for (row in allOutputData["monthDataMat"]) {
        insertMetric("powerflowReportTable", "", allOutputData["monthDataMat"][row])
    }

    for (row in allOutputData["monthDataPart"]) {
        insertMetric("moneyReportTable", "", allOutputData["monthDataPart"][row])
    }

})(LineChart, BarChart);