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

    // Make sure the file is required on prerun.
    if (modelStatus == "preRun" || modelStatus == "stopped") {
        gebi('demandCurveFile').setAttribute('required', 'required')
    }
    else {
    }
    // File handler function.
    function handle_files(files) {
        // read file to a hidden input field
        reader = new FileReader()
        reader.readAsText(files[0])
        reader.onload = loaded
        function loaded(evt) {
            evt.target.result
            gebi("demandCurve").value = reader.result
        }
    }

    function insertMetric(tableId, name, vector) {
        // Add a vector to a table as a row.
        table = gebi(tableId)
        newRow = table.insertRow()
        newRow.insertCell().innerHTML = "<div id=\"metric\">" + name + "</div>"
        for (i = 0; i < vector.length; i++) {
            cell = newRow.insertCell()
            cell.innerHTML = delimitNumbers(vector[i].toFixed(0))
        }
    }

    function insertDollarMetric(tableId, name, vector) {
        // Add a vector to a table as a row.
        table = gebi(tableId)
        newRow = table.insertRow()
        newRow.insertCell().innerHTML = "<div id=\"metric\">" + name + "</div>"
        for (i = 0; i < vector.length; i++) {
            cell = newRow.insertCell()
            cell.innerHTML = "$" + delimitNumbers(vector[i].toFixed(0))
        }
    }

    insertMetric("monthlySummaryTable", "Existing Demand (kW)", allOutputData.monthlyDemand)
    insertMetric("monthlySummaryTable", "Demand with Battery (kW)", allOutputData.monthlyDemandRed)
    insertMetric("monthlySummaryTable", "Reduction Amount (kW)", allOutputData.ps)
    insertMetric("monthlySummaryTable", "kWh to Full-Battery (kW)", allOutputData.kWhtoRecharge)
    insertDollarMetric("monthlySummaryTable", "Value of Reduction ($)", allOutputData.benefitMonthly)
    insertDollarMetric("monthlySummaryTable", "Cost to Recharge Battery ($)", allOutputData.costtoRecharge)
    insertDollarMetric("monthlySummaryTable", "Net Benefit ($)", allOutputData.benefitNet)


    table = gebi("monthlySummaryTable")
    newRow = table.insertRow()
    newRow.insertCell().innerHTML = ""
    newRow = table.insertRow()
    newRow.insertCell().innerHTML = "<div id=\"SPP\">Financial Calculations:</div>"
    newRow.insertCell().innerHTML = "<div id=\"SPP\">NPV:</div>"
    cell = newRow.insertCell()
    cell.innerHTML = "$" + delimitNumbers(allOutputData.NPV.toFixed(0))
    cell = newRow.insertCell()
    cell.innerHTML + ""
    newRow.insertCell().innerHTML = "<div id=\"SPP\">SPP:</div>"
    cell = newRow.insertCell()
    cell.innerHTML = delimitNumbers(allOutputData.SPP.toFixed(3))
    var axisTime = new Date(Date.parse(allOutputData.startDate) - 3600000);
    var timeStamps = allOutputData.demand.map(function (a) {
        axisTime = new Date(axisTime.getTime() + 3600000);
        return axisTime;
    });

    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 750,
        "#demandBattChart",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.demand,
                data2: allOutputData.demandAfterBattery,
                data3: allOutputData.batteryDischargekW
            },
            colors: {
                data1: "red",
                data2: "purple",
                data3: "orange"
            },
            names: {
                data1: "Demand",
                data2: "Demand After Battery",
                data3: "Battery Discharge"
            }

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Power (W)',
        position: 'outer-middle'
    };
    chartOptions.options.grid.y = {
        show: true,
        lines: [
            {
                text: "Max Power:" + allOutputData.batteryDischargekWMax / 1000 + "kW",
                value: allOutputData.batteryDischargekWMax,
                class: 'nameplate',
                position: 'start'
            }
        ]
    };
    c3.generate(chartOptions.options);

    var dodFactor = 100 - parseFloat(allInputData.dodFactor);
    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 250,
        "#batterySocChart",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.batterySoc
            },
            colors: {
                data1: "gray"
            },
            names: {
                data1: "Battery SoC"
            }

        }
    );
    chartOptions.options.axis.y = {
        max: 100,
        min: 0,
        tick: {
            outer: false,
            format: function (d) {
                if (d % 25 === 0) {
                    return d;
                }
            }
        },
        label: {
            text: 'SoC (%)',
            position: 'outer-middle'
        }
    };
    chartOptions.options.grid.y = {
        show: true,
        lines: [
            {
                text: "Max specified DOD:" + (100 - allInputData.dodFactor) + "%",
                value: dodFactor,
                class: 'gridLines',
                position: 'start'
            }
        ]
    };
    chartOptions.options.legend = {
        show: false
    };
    chartOptions.options.axis.x.label = {
        text: "Cycle Equivalents:" + delimitNumbers(allOutputData.cycleEquivalents.toFixed(1))
    };
    c3.generate(chartOptions.options);


    var barChartOptions = new BarChartModule.C3BarChartOptions(
        980, 250,
        "#cashFlowChartDiv",
        {
            json: {
                data1: allOutputData.netCashflow,
                data2: allOutputData.cumulativeCashflow
            },
            names: {
                data1: "Net Benefits",
                data2: "Cumulative Return"
            },
            type: 'bar',
            types: {
                data2: 'line'
            }
        },
        []);
    barChartOptions.options.bar = {
        width: 15
    };
    barChartOptions.options.point = {
        r: 3
    };
    barChartOptions.options.axis.x = {
        label: {
            text: "NPV:$" + delimitNumbers(allOutputData.NPV.toFixed(0)) + "; SPP:" + allOutputData.SPP.toFixed(3)
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


})(LineChart, BarChart);