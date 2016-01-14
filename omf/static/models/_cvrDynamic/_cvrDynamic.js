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
/*
		 * Global setting of Highcharts
		 */
	function init() {
			// If we have input, put it back.
			if (allInputData != null) {
				restoreInputs()
				$("#modelName").prop("readonly", true)
			}
			// Depending on status, show different things.
			if (modelStatus == "finished") {
				console.log("FINISHED")
				$(".postRun").css('display', 'block')
				$(".postRunInline").css('display', 'inline-block')
			} else if (modelStatus == "running") {
				console.log("RUNNING")
				$(".running").css('display', 'block')
				$(".runningInline").css('display', 'inline-block')
				$("input").prop("readonly", true)
				$("select").prop("disabled", true)
			} else /* Stopped */ {
				if (allInputData != null) {
					$(".stopped").show()
					$(".stoppedInline").show()
				} else {
					console.log("PRERUN")
					$(".preRun").css('display', 'inline-block')
				}
			}
		}

	var timeStamps = allOutputData.timeStamps.map(function (a) {
        return new Date(a)
    });

	var barChartOptions = new BarChartModule.C3BarChartOptions(
        980, 200,
        "#totalEnergyReport",
        {
            json: {
                data1: [allOutputData["withCVRLoad"],allOutputData["noCVRLoad"]],
                data2: [allOutputData["withCVRLosses"],allOutputData["noCVRLosses"]]
            },
            colors: {
                data1: "darkorange",
                data2: "orangered"
            },
            names: {
                data1: "Load",
                data2: "Losses"
            }
        },
        ["With CVR", "No CVR"]);
    barChartOptions.options.axis.y.label = {
        text: 'Total Load and Losses (MWh)',
        position: 'outer-middle'
    };
    barChartOptions.options.bar = {
        width: 40
    };
    c3.generate(barChartOptions.options);

	var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 200,
        "#realPowerflow",
        {
			x: 'x',
            json: {
				x: timeStamps,
                data1: allOutputData["withCVRPower"],
				data2: allOutputData["noCVRPower"]
            },
            colors: {
                data1: "blue",
				data2: "Green"
            },
            names: {
                data1: "With IVVC",
				data2: "With IVVC"
            }
        }
    );
    chartOptions.options.axis.y.label = {
        text: 'substation real power (W)',
        position: 'outer-middle'
    };
    c3.generate(chartOptions.options);

var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 200,
        "#minMaxVoltRecord",
        {
			x: 'x',
            json: {
				x: timeStamps,
                data1: allOutputData["withCVRMeanVolt"],
				data2: allOutputData["withCVRHighVolt"],
				data3: allOutputData["withCVRLowVolt"],
				data4: allOutputData["noCVRMeanVolt"],
				data5: allOutputData["noCVRHighVolt"],
				data6: allOutputData["noCVRLowVolt"]
            },
            colors: {
                data1: "blue",
				data2: "DarkBlue",
				data3: "LightBlue",
				data4: "Green",
				data5: "DarkGreen",
				data6: "LightGreen"
            },
            names: {
                data1: "With IVVC Mean Volts",
				data2: "With IVVC High Volts",
				data3: "With IVVC Low Volts",
				data4: "No IVVC Mean Volts",
				data5: "No IVVC High Volts",
				data6: "No IVVC Low Volts"
            },
			regions: {
				'data4': [{'style':'dashed'}],
				'data5': [{'style':'dashed'}],
				'data6': [{'style':'dashed'}]
			}

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Voltages',
        position: 'outer-middle'
    };
    c3.generate(chartOptions.options);

	var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 200,
        "#tapStatus",
        {
			x: 'x',
            json: {
				x: timeStamps,
                data1: allOutputData["withCVRTaps"]["A"],
				data2: allOutputData["withCVRTaps"]["B"],
				data3: allOutputData["withCVRTaps"]["C"],
				data4: allOutputData["noCVRTaps"]["A"],
				data5: allOutputData["noCVRTaps"]["B"],
				data6: allOutputData["noCVRTaps"]["C"]
            },
            colors: {
                data1: "blue",
				data2: "DarkBlue",
				data3: "LightBlue",
				data4: "Green",
				data5: "DarkGreen",
				data6: "LightGreen"
            },
            names: {
                data1: "With IVVC A",
				data2: "With IVVC B",
				data3: "With IVVC C",
				data4: "No IVVC A",
				data5: "No IVVC B",
				data6: "No IVVC C"
            },
			regions: {
				'data4': [{'style':'dashed'}],
				'data5': [{'style':'dashed'}],
				'data6': [{'style':'dashed'}]
			}

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Tap Positions',
        position: 'outer-middle'
    };
    c3.generate(chartOptions.options);

	var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 200,
        "#CapSwitchStat",
        {
			x: 'x',
            json: {
				x: timeStamps,
                data1: allOutputData["withCVRCapSwitch"]["A"],
				data2: allOutputData["withCVRCapSwitch"]["B"],
				data3: allOutputData["withCVRCapSwitch"]["C"],
				data4: allOutputData["noCVRCapSwitch"]["A"],
				data5: allOutputData["noCVRCapSwitch"]["B"],
				data6: allOutputData["noCVRCapSwitch"]["C"]
            },
            colors: {
                data1: "blue",
				data2: "DarkBlue",
				data3: "LightBlue",
				data4: "Green",
				data5: "DarkGreen",
				data6: "LightGreen"
            },
            names: {
                data1: "With IVVC A",
				data2: "With IVVC B",
				data3: "With IVVC C",
				data4: "No IVVC A",
				data5: "No IVVC B",
				data6: "No IVVC C"
            },
			regions: {
				'data4': [{'style':'dashed'}],
				'data5': [{'style':'dashed'}],
				'data6': [{'style':'dashed'}]
			}

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Switch Status',
        position: 'outer-middle'
    };
    c3.generate(chartOptions.options);

	var chartOptions = new LineChartModule.C3LineChartOptions(
        980, 200,
        "#voltagePlots",
        {
			x: 'x',
            json: {
				x: timeStamps,
                data1: allOutputData["withCVRSubVolts"]["A"],
				data2: allOutputData["withCVRSubVolts"]["B"],
				data3: allOutputData["withCVRSubVolts"]["C"],
				data4: allOutputData["noCVRSubVolts"]["A"],
				data5: allOutputData["noCVRSubVolts"]["B"],
				data6: allOutputData["noCVRSubVolts"]["C"]
            },
            colors: {
                data1: "blue",
				data2: "DarkBlue",
				data3: "LightBlue",
				data4: "Green",
				data5: "DarkGreen",
				data6: "LightGreen"
            },
            names: {
                data1: "With IVVC A",
				data2: "With IVVC B",
				data3: "With IVVC C",
				data4: "No IVVC A",
				data5: "No IVVC B",
				data6: "No IVVC C"
            },
			regions: {
				'data4': [{'style':'dashed'}],
				'data5': [{'style':'dashed'}],
				'data6': [{'style':'dashed'}]
			}

        }
    );
    chartOptions.options.axis.y.label = {
        text: 'Voltages',
        position: 'outer-middle'
    };
    c3.generate(chartOptions.options);


    var barChartOptions = new BarChartModule.C3BarChartOptions(
        980, 200,
        "#spendReport",
        {
            json: {
                data1: $.map(allOutputData["energyLostDollars"], function(key, value){return key}),
                data2: $.map(allOutputData["lossRedDollars"], function(key, value){return key}),
                data3: $.map(allOutputData["peakSaveDollars"], function(key, value){return key})
            },
            colors: {
                data1: "red",
                data2: "green",
                data3: "blue"
            },
            names: {
                data1: "Energy Reduction",
                data2: "Losses Reduction",
                data3: "Peak Reduction"
            }
        },
        allOutputData["simMonthList"]);
    barChartOptions.options.axis.y.label = {
        text: 'Utility Savings ($)',
        position: 'outer-middle'
    };
    barChartOptions.options.bar = {
        width: 40
    };
    c3.generate(barChartOptions.options);

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
                data1: "Annual Savings"
            }

        }
    );
    chartOptions.options.axis.x = {};
    chartOptions.options.tooltip.format.title= function (d) {
            return d;
        };
    chartOptions.options.axis.y.label = {
        text: 'Cumulative Savings ($)',
        position: 'outer-middle'
    };
    chartOptions.options.point = {
        r: 3
    };
    c3.generate(chartOptions.options);

})(LineChart, BarChart);