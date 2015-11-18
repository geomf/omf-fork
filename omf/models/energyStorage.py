# Portions Copyrights (C) 2015 Intel Corporation
''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import sys
import shutil
import datetime
import traceback
import csv
import os
import json
from dateutil.parser import parse
from numpy import npv
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import renderAndShow, getStatus as getStatusMeta
import logging

logger = logging.getLogger(__name__)

# TODO remove this later.
import matplotlib.pyplot as plt

# OMF imports
sys.path.append(__metaModel__._omfDir)
from omf.common.plot import Plot

template = None

def renderTemplate(template, fs, modelDir="", absolutePaths=False, datastoreNames={}):
    # Our HTML template for the interface:
    with fs.open("models/energyStorage.html") as tempFile:
        template = Template(tempFile.read())
    return __metaModel__.renderTemplate(template, fs, modelDir, absolutePaths, datastoreNames)

# def quickRender(template, modelDir="", absolutePaths=False, datastoreNames={}):
# 	''' Presence of this function indicates we can run the model quickly via a public interface. '''
# return __metaModel__.renderTemplate(template, modelDir, absolutePaths,
# datastoreNames, quickRender=True)


def getStatus(modelDir, fs):
    return getStatusMeta(modelDir, fs)


def run(modelDir, inputDict, fs):
    ''' Run the model in its directory. '''
    # Delete output file every run if it exists
    logger.info("Running energyStorage model... modelDir: %s; inputDict: %s", modelDir, inputDict)
    try:
        fs.remove(pJoin(modelDir, "allOutputData.json"))
    except Exception, e:
       pass
    # Check whether model exist or not
    try:
        if not fs.exists(modelDir):
            fs.create_dir(modelDir)
            inputDict["created"] = str(datetime.datetime.now())
        fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
        # Ready to run.
        startTime = datetime.datetime.now()
        outData = {}
        # Get variables.
        cellCapacity = float(inputDict['cellCapacity'])
        (cellCapacity, dischargeRate, chargeRate, cellQuantity, demandCharge, cellCost) = \
            [float(inputDict[x]) for x in ('cellCapacity', 'dischargeRate',
                                           'chargeRate', 'cellQuantity', 'demandCharge', 'cellCost')]
        battEff = float(inputDict.get("batteryEfficiency", 92)) / 100.0 * float(inputDict.get(
            "inverterEfficiency", 92)) / 100.0 * float(inputDict.get("inverterEfficiency", 92)) / 100.0
        discountRate = float(inputDict.get('discountRate', 2.5)) / 100.0
        elecCost = float(inputDict.get('elecCost', 0.07))
        # CHANGE: dodFactor, DEMANDCHARGEMONTHLY
        dodFactor = float(inputDict.get('dodFactor', 85)) / 100.0
        projYears = int(inputDict.get('projYears', 10))
        # Put demand data in to a file for safe keeping.
        fs.save(pJoin(modelDir, "demand.csv"), inputDict['demandCurve'])
        # Start running battery simulation.
        # CHANGE
        # battCapacity = cellQuantity * cellCapacity
        battCapacity = cellQuantity * cellCapacity * dodFactor
        battDischarge = cellQuantity * dischargeRate
        battCharge = cellQuantity * chargeRate
        # Most of our data goes inside the dc "table"
        dc = [{'datetime': parse(row['timestamp']), 'power': int(
            row['power'])} for row in csv.DictReader(fs.open(pJoin(modelDir, "demand.csv")))]
        for row in dc:
            row['month'] = row['datetime'].month - 1
            row['weekday'] = row['datetime'].weekday
        outData['startDate'] = dc[0]['datetime'].isoformat()
        ps = [battDischarge for x in range(12)]
        dcGroupByMonth = [
            [t['power'] for t in dc if t['datetime'].month - 1 == x] for x in range(12)]
        monthlyPeakDemand = [max(dcGroupByMonth[x]) for x in range(12)]
        capacityLimited = True
        while capacityLimited:
            battSoC = battCapacity  # Battery state of charge; begins full.
            # Depth-of-discharge every month, depends on dodFactor.
            battDoD = [battCapacity for x in range(12)]
            for row in dc:
                month = int(row['datetime'].month) - 1
                powerUnderPeak = monthlyPeakDemand[
                    month] - row['power'] - ps[month]
                isCharging = powerUnderPeak > 0
                isDischarging = powerUnderPeak <= 0
                charge = isCharging * min(
                    # Charge rate <= new monthly peak - row['power']
                    powerUnderPeak * battEff,
                    # Charge rate <= battery maximum charging rate.
                    battCharge,
                    battCapacity - battSoC)  # Charge rage <= capacity remaining in battery.
                discharge = isDischarging * min(
                    # Discharge rate <= new monthly peak - row['power']
                    abs(powerUnderPeak),
                    # Discharge rate <= battery maximum charging rate.
                    abs(battDischarge),
                    abs(battSoC + .001))  # Discharge rate <= capacity remaining in battery.
                # (Dis)charge battery
                battSoC += charge
                battSoC -= discharge
                # Update minimum state-of-charge for this month.
                battDoD[month] = min(battSoC, battDoD[month])
                row['netpower'] = row['power'] + charge / battEff - discharge
                row['battSoC'] = battSoC
            capacityLimited = min(battDoD) < 0
            ps = [ps[month] - (battDoD[month] < 0) for month in range(12)]
        dcThroughTheMonth = [
            [t for t in iter(dc) if t['datetime'].month - 1 <= x] for x in range(12)]
        hoursThroughTheMonth = [
            len(dcThroughTheMonth[month]) for month in range(12)]
        peakShaveSum = sum(ps)
        outData['SPP'] = (cellCost * cellQuantity) / \
            (peakShaveSum * demandCharge)
        cashFlowCurve = [
            peakShaveSum * demandCharge for year in range(projYears)]
        cashFlowCurve[0] -= (cellCost * cellQuantity)
        outData['netCashflow'] = cashFlowCurve
        outData['cumulativeCashflow'] = [
            sum(cashFlowCurve[0:i + 1]) for i, d in enumerate(cashFlowCurve)]
        outData['NPV'] = npv(discountRate, cashFlowCurve)
        outData['demand'] = [t['power'] * 1000.0 for t in dc]
        outData['demandAfterBattery'] = [t['netpower'] * 1000.0 for t in dc]
        # outData['batterySoc'] = [t['battSoC']/battCapacity*100.0 for t in dc]
        outData['batterySoc'] = [t['battSoC'] / battCapacity *
                                 100.0 * dodFactor + (100 - 100 * dodFactor) for t in dc]
        # Estimate number of cyles the battery went through.
        SoC = outData['batterySoc']
        outData['cycleEquivalents'] = sum(
            [SoC[i] - SoC[i + 1] for i, x in enumerate(SoC[0:-1]) if SoC[i + 1] < SoC[i]]) / 100.0
        # Output some matplotlib results as well.
        plt.plot([t['power'] for t in dc])
        plt.plot([t['netpower'] for t in dc])
        plt.plot([t['battSoC'] for t in dc])
        for month in range(12):
            plt.axvline(hoursThroughTheMonth[month])
        Plot.save_fig(plt, pJoin(modelDir, "plot.png"))
        # DRDAN: Summary of results
        outData['months'] = ["Jan", "Feb", "Mar", "Apr", "May",
                             "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        totMonNum = []
        monthlyDemand = []
        for x in range(0, len(dcGroupByMonth)):
            totMonNum.append(sum(dcGroupByMonth[x]) / 1000)
            monthlyDemand.append([outData['months'][x], totMonNum[x]])
        outData['monthlyDemand'] = totMonNum
        outData['ps'] = ps		# TODO: [Battery Capacity Left]
        outData['monthlyDemandRed'] = [
            totMonNum - ps for totMonNum, ps in zip(totMonNum, ps)]
        outData['benefitMonthly'] = [x * demandCharge for x in outData['ps']]
        outData['kWhtoRecharge'] = [battCapacity - x for x in outData['ps']]
        outData['costtoRecharge'] = [
            elecCost * x for x in outData['kWhtoRecharge']]
        benefitMonthly = outData['benefitMonthly']
        costtoRecharge = outData['costtoRecharge']
        outData['benefitNet'] = [benefitMonthly - costtoRecharge for benefitMonthly,
                                 costtoRecharge in zip(benefitMonthly, costtoRecharge)]
        # Battery KW
        demandAfterBattery = outData['demandAfterBattery']
        demand = outData['demand']
        outData['batteryDischargekW'] = [demand - demandAfterBattery for demand,
                                         demandAfterBattery in zip(demand, demandAfterBattery)]
        outData['batteryDischargekWMax'] = max(outData['batteryDischargekW'])
        # Stdout/stderr.
        outData["stdout"] = "Success"
        outData["stderr"] = ""
        # Write the output.
        fs.save(pJoin(modelDir, "allOutputData.json"), json.dumps(outData, indent=4))
        # Update the runTime in the input file.
        endTime = datetime.datetime.now()
        inputDict["runTime"] = str(
            datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
        fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
    except:
        # If input range wasn't valid delete output, write error to disk.
        thisErr = traceback.format_exc()
        print 'ERROR IN MODEL', modelDir, thisErr
        inputDict['stderr'] = thisErr
        with open(os.path.join("tmp", 'stderr.txt'), 'w') as errorFile:
            errorFile.write(thisErr)
        fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
        try:
            fs.remove(pJoin(modelDir, "allOutputData.json"))
        except Exception, e:
           pass


def cancel(modelDir):
    ''' This model runs so fast it's pointless to cancel a run. '''
    pass


def _tests():
    # Variables
    from .. import filesystem
    fs = filesystem.Filesystem().fs
    workDir = pJoin(__metaModel__._omfDir, "data", "Model")
    inData = {
        "batteryEfficiency": "92",
        "cellCapacity": "100",
        "discountRate": "2.5",
        "created": "2015-06-12 17:20:39.308239",
        "dischargeRate": "50",
        "modelType": "energyStorage",
        "chargeRate": "50",
        "demandCurve": fs.open(pJoin(__metaModel__._omfDir, "scratch", "batteryModel", "OlinBeckenhamScada.csv")).read(),
        "cellCost": "25000",
        "cellQuantity": "3",
        "runTime": "0:00:03",
        "projYears": "10",
        "demandCharge": "50"}
    modelLoc = pJoin(workDir, "admin", "Automated energyStorage Testing")
    # Blow away old test results if necessary.
    try:
        shutil.rmtree(modelLoc)
    except:
        # No previous test results.
        pass
    # No-input template.
    renderAndShow(template, fs)
    # Run the model.
    run(modelLoc, inData, fs)
    # Show the output.
    renderAndShow(template, fs, modelDir=modelLoc)
    # # Delete the model.
    # time.sleep(2)
    # shutil.rmtree(modelLoc)

if __name__ == '__main__':
    _tests()
