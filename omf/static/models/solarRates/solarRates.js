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
    // Clean up the non-ISO date strings we get.
    function dateOb(inStr) {
        return Date.parse(inStr.replace(/-/g, "/"))
    }

    var timeStamps = allOutputData.timeStamps.map(function (a) {
        return new Date(a)
    });

    pointStart = dateOb(allOutputData.timeStamps[0])
    pointInterval = dateOb(allOutputData.timeStamps[1]) - pointStart
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

    var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 250,
        "#powerTimeSeries",
        {
            x: 'x',
            json: {
                x: timeStamps,
                data1: allOutputData.powerOutputAc

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
        text: 'Power (W)',
        position: 'outer-middle'
    };
    chartOptions.options.legend = {
        show: false
    };
    c3.generate(chartOptions.options);

    var barCategory = allOutputData.totalGeneration.map(function (a) {
        return a[0];
    });
    var barValuesGeneration = allOutputData.totalGeneration.map(function (a) {
        return a[1];
    });
    var barValuesSolar = allOutputData.totalsolarmonthly.map(function (a) {
        return a[1];
    });
    var barChartOptions = new BarChartModule.C3BarChartOptions(
        980, 250,
        "#monthlyPerformanceDiv",
        {
            json: {
                data1: barValuesGeneration,
                data2: barValuesSolar
            },
            colors: {
                data1: "orange",
                data2: "green"
            },
            names: {
                data1: "From Solar",
                data2: "From G&T"
            },
            type: 'bar'
        },
        barCategory);
    barChartOptions.options.axis.y.label = {
        text: 'Energy (Wh)',
        position: 'outer-middle'
    };
    barChartOptions.options.bar = {
        width: 15
    };
    c3.generate(barChartOptions.options);

    function convertunits(nStr, places) {
        // Divide nStr by 10^places and return the integer.
        nStr += ''
        x = nStr.split('.')
        x1 = x[0]
        xint = parseInt(x1) / (Math.pow(10, places))
        return xint
    }

    gebi("patronageCashLabel").innerHTML = "$" + delimitNumbers(allOutputData.Solar.patCapital.toFixed(0))
    gebi("lossesEnergyLabel").innerHTML = delimitNumbers(convertunits(allOutputData.Solar.losses, 3).toFixed(0)) + " MWh"
    gebi("vendorCashLabel").innerHTML = "$" + delimitNumbers(allOutputData.BAU.nonPowerCosts.toFixed(0))
    gebi("gtEnergyLabel").innerHTML = delimitNumbers(convertunits(allOutputData.Solar.totalKWhPurchased, 3).toFixed(0)) + " MWh"
    gebi("gtCashLabel").innerHTML = "$" + delimitNumbers(allOutputData.Solar.costPurchasedPower.toFixed(0))
    gebi("vendorCashLabel").innerHTML = "$" + delimitNumbers(allOutputData.BAU.nonPowerCosts.toFixed(0))
    gebi("solarConEnergyLabel").innerHTML = delimitNumbers(convertunits(allOutputData.Solar.solarResSold, 3).toFixed(0)) + " MWh"
    gebi("solarConCashLabel").innerHTML = "$" + delimitNumbers(allOutputData.Solar.solarResRev.toFixed(0))
    gebi("nonSolarConEnergyLabel").innerHTML = delimitNumbers(convertunits(allOutputData.Solar.resNonSolarKWhSold, 3).toFixed(0)) + " MWh"
    gebi("nonSolarConCashLabel").innerHTML = "$" + delimitNumbers(allOutputData.Solar.resNonSolarRev.toFixed(0))
    gebi("commConEnergyLabel").innerHTML = delimitNumbers(convertunits(allOutputData.BAU.nonResKWhSold, 3).toFixed(0)) + " MWh"
    gebi("commConCashLabel").innerHTML = "$" + delimitNumbers(allOutputData.Solar.nonResRev.toFixed(0))
    gebi("panelsEnergyLabel").innerHTML = delimitNumbers(convertunits(allOutputData.Solar.annualSolarGen, 3).toFixed(0)) + " MWh"
    gebi("panelsCashLabel").innerHTML = "$" + delimitNumbers(allOutputData.Solar.costSolarGen.toFixed(0))
    gebi("avgNonSolarBill").innerHTML = "Avg Bill " + delimitNumbers(allOutputData.Solar.avgMonthlyBillNonSolarCus.toFixed(0)) + " $/Month"
    gebi("avgSolarBill").innerHTML = "Avg Bill " + delimitNumbers(allOutputData.Solar.avgMonthlyBillSolarCus.toFixed(0)) + " $/Month"
    gebi("currentRate").innerHTML = "BAU Costs " + delimitNumbers(allOutputData.BAU.costofService.toFixed(3)) + " $/kWh"
    gebi("costofService").innerHTML = "Solar Costs " + delimitNumbers(allOutputData.Solar.costofService.toFixed(3)) + " $/kWh"

    // Set all the values in the above table by mapping ID<->allOutput.
    table = gebi("bauVersusSolarTable")
    rows = table.children[0].children
    for (i = 1; i < rows.length; i++) {
        tds = rows[i].children
        tds[2].innerHTML = delimitNumbers(allOutputData.BAU[tds[2].id.substring(4)].toFixed(0))
        tds[3].innerHTML = delimitNumbers(allOutputData.Solar[tds[3].id.substring(4)].toFixed(0))
    }


    //insertMetric("monthlySummaryTable","Month", allOutputData.monthlyGeneration.map(function(x){return x[0]}))
    table = gebi("monthlySummaryTable")
    newRow = table.insertRow()
    newRow.insertCell().innerHTML = "Month"
    for (i = 0; i < allOutputData.monthlyGeneration.map(function (x) {
        return x[1]
    }).length; i++) {
        cell = newRow.insertCell()
        cell.innerHTML = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][i]
    }
    insertMetric("monthlySummaryTable", "No. Consumer Served", allOutputData.monthlyNoConsumerServedSales.map(function (x) {
        return x[1]
    }))
    insertMetric("monthlySummaryTable", "Single Residential PV System Generation(kWh)", allOutputData.monthlyGeneration.map(function (x) {
        return x[1] / 1000
    }))
    insertMetric("monthlySummaryTable", "Total Residential PV Generation(kWh)", allOutputData.totalGeneration.map(function (x) {
        return x[1]
    }))
    insertMetric("monthlySummaryTable", "KWh Sold", allOutputData.monthlyKWhSold.map(function (x) {
        return x[1]
    }))
    insertMetric("monthlySummaryTable", "Revenue", allOutputData.monthlyRevenue.map(function (x) {
        return x[1]
    }))
    insertMetric("monthlySummaryTable", "Total KWh Sold", allOutputData.totalKWhSold.map(function (x) {
        return x[1]
    }))
    insertMetric("monthlySummaryTable", "Total Revenue from Sales of Electric Energy", allOutputData.totalRevenue.map(function (x) {
        return x[1]
    }))


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
        text: 'Irradiance (W/m^2)',
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

})(LineChart, BarChart);