﻿#!/usr/bin/env python

import os
import re
import __util__ as util
from copy import copy
import math
import json
from jinja2 import Template

with open('./reports/monetizationConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read()

def outputHtml(analysisObject, studyList):
	# Set general run data:
	resolution = analysisObject.simLengthUnits
	startTime = analysisObject.simStartDate
	# Get the report input:
	inputData = {}
	try:
		reportConfig = [rep for rep in analysisObject.reports if rep.get('reportType','') == 'monetization'][0]
	except:
		reportConfig = {}
	inputData['distrEnergyRate'] = float(reportConfig.get('distrEnergyRate',0))
	inputData['distrCapacityRate'] = float(reportConfig.get('distrCapacityRate',0))
	inputData['equipAndInstallCost'] = float(reportConfig.get('equipAndInstallCost',0))
	inputData['opAndMaintCost'] = float(reportConfig.get('opAndMaintCost',0))
	# Pull in the power data:
	studyDict = {}
	timeStamps = []
	for study in studyList:
		studyDict[study.name] = {}
		studyJson = study.outputJson
		timeStamps = studyJson.get('timeStamps',[])
		studyDict[study.name]['Power'] = studyJson.get('Consumption',{}).get('Power',[])
	# What percentage of a year did we simulate?
	intervalMap = {'minutes':60, 'hours':3600, 'days':86400}
	inputData['yearPercentage'] = intervalMap[resolution]*len(timeStamps)/(365*24*60*60.0)
	# Money power graph:
	monPowParams = util.defaultGraphObject(resolution, startTime)
	monPowParams['chart']['height'] = 200
	monPowParams['chart']['width'] = 500
	monPowParams['chart']['renderTo'] = 'monetizedPowerTimeSeries'
	monPowParams['chart']['type'] = 'line'
	monPowParams['yAxis']['title']['text'] = 'Capacity Cost ($)'
	for study in studyDict:
		color = util.rainbow(studyDict,study,['salmon','red','darkred','crimson','firebrick','indianred'])
		monPowParams['series'].append({'name':study,'data':[],'color':color})
	# Money energy graph:
	monEnergyParams = util.defaultGraphObject(resolution, startTime)
	monEnergyParams['chart']['height'] = 200
	monEnergyParams['chart']['width'] = 500
	monEnergyParams['chart']['renderTo'] = 'monetizedEnergyBalance'
	monEnergyParams['chart']['type'] = 'line'
	monEnergyParams['yAxis']['title']['text'] = 'Energy Cost ($)'
	for study in studyDict:
		color = util.rainbow(studyDict,study,['goldenrod','orange','darkorange','gold','chocolate'])
		monEnergyParams['series'].append({'name':study,'data':[],'color':color})
	# Cost growth graph:
	savingsGrowthParams = util.defaultGraphObject(resolution, startTime)
	savingsGrowthParams['chart']['height'] = 200
	savingsGrowthParams['chart']['width'] = 1000
	savingsGrowthParams['chart']['renderTo'] = 'costGrowthContainer'
	savingsGrowthParams['chart']['type'] = 'line'
	savingsGrowthParams['yAxis']['title']['text'] = 'Cumulative Savings ($)'
	savingsGrowthParams['xAxis'] = 	{'type':'linear', 'tickColor':'gray', 'lineColor':'gray', 'title':{'text':'Years After Install'}}
	savingsGrowthParams['plotOptions']['series'] = {'shadow':False}
	for study in studyDict:
		color = util.rainbow(studyDict,study,['dimgray','darkgray','gainsboro','silver'])
		savingsGrowthParams['series'].append({'name':study,'data':[],'color':color})
		savingsGrowthParams['xAxis']['plotLines'] = [{'color':'silver','width':1,'value':inputData['yearPercentage']}]
	# Get the template in.
	with open('./reports/monetizationOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(monPowParams=json.dumps(monPowParams), monEnergyParams=json.dumps(monEnergyParams), savingsGrowthParams=json.dumps(savingsGrowthParams),
							inputData=json.dumps(inputData), studyDict=json.dumps(studyDict), timeStamps = json.dumps(timeStamps))
