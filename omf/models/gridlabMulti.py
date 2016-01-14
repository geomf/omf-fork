# Portions Copyright (C) 2015 Intel Corporation
''' Powerflow results for one Gridlab instance. '''

import sys
import shutil
import os
import datetime
import multiprocessing
import pprint
import json
import math
import traceback
import __metaModel__
import logging
from os.path import join as pJoin
from os.path import split as pSplit
from pyhdfs import HdfsFileNotFoundException
from jinja2 import Template
from __metaModel__ import renderAndShow, cancel, roundSig, getStatus

import omf
from omf.solvers import gridlabd
from omf.weather import zipCodeToClimateName
from flask import session

logger = logging.getLogger(__name__)
sys.path.append(__metaModel__._omfDir)
pp = pprint.PrettyPrinter(indent=4)

from omf import feeder


template = None

def renderTemplate(template, fs, modelDir="", absolutePaths=False, datastoreNames={}):
    ''' Render the model template to an HTML string.
    By default render a blank one for new input.
    If modelDir is valid, render results post-model-run.
    If absolutePaths, the HTML can be opened without a server. '''

    # Our HTML template for the interface:
    with fs.open("models/gridlabMulti.html") as tempFile:
        template = Template(tempFile.read())

    try:
        inJson = json.load(fs.open(pJoin(modelDir, "allInputData.json")))
        modelPath, modelName = pSplit(modelDir)
        deepPath, user = pSplit(modelPath)
        inJson["modelName"] = modelName
        inJson["user"] = user
        allInputData = json.dumps(inJson)
    except HdfsFileNotFoundException:
        allInputData = None
    except IOError:
        allInputData = None
    try:
        allOutputData = fs.open(pJoin(modelDir, "allOutputData.json")).read()
    except HdfsFileNotFoundException:
        allOutputData = None
    except IOError:
        allOutputData = None
    if absolutePaths:
        # Parent of current folder.
        pathPrefix = __metaModel__._omfDir
    else:
        pathPrefix = ""
    feederList = []
    feederIDs = []
    try:
        inputDict = json.load(fs.open(pJoin(modelDir, "allInputData.json")))
        for key in inputDict:
            if key.startswith("feederName"):
                feederIDs.append(key)
                feederList.append(inputDict[key])
    except HdfsFileNotFoundException:
        pass
    except IOError:
        pass
    with open('templates/footer.html', 'r') as footer_file:
        footer = footer_file.read()
    return template.render(allInputData=allInputData,
                           allOutputData=allOutputData, modelStatus=getStatus(modelDir, fs), pathPrefix=pathPrefix,
                           datastoreNames=datastoreNames, feederIDs=feederIDs, feederList=feederList, footer=footer)


def run(modelDir, inputDict, fs):
    ''' Run the model in a separate process. web.py calls this to run the model.
    This function will return fast, but results take a while to hit the file system.'''
    # Check whether model exist or not
    logging.info("Running gridlabMulti model... modelDir: %s; inputDict: %s", modelDir, inputDict)
    if not os.path.isdir(modelDir):
        os.makedirs(modelDir)
        inputDict["created"] = str(datetime.datetime.now())
    # MAYBEFIX: remove this data dump. Check showModel in web.py and
    # renderTemplate()
    with open(pJoin(modelDir, "allInputData.json"), "w") as inputFile:
        json.dump(inputDict, inputFile, indent=4)
    fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
    # If we are re-running, remove output:
    try:
        os.remove(pJoin(modelDir, "allOutputData.json"))
    except:
        pass
    backProc = multiprocessing.Process(
        target=runForeground, args=(modelDir, inputDict, fs))
    backProc.start()
    print "SENT TO BACKGROUND", modelDir
    with open(pJoin(modelDir, "PPID.txt"), "w+") as pPidFile:
        pPidFile.write(str(backProc.pid))


def runForeground(modelDir, inputDict, fs):
    ''' Run the model in its directory. WARNING: GRIDLAB CAN TAKE HOURS TO COMPLETE. '''
    print "STARTING TO RUN", modelDir
    beginTime = datetime.datetime.now()
    feederList = []
    # Get prepare of data and clean workspace if re-run, If re-run remove all
    # the data in the subfolders
    for dirs in os.listdir(modelDir):
        if os.path.isdir(pJoin(modelDir, dirs)):
            shutil.rmtree(pJoin(modelDir, dirs))
    # Get each feeder, prepare data in separate folders, and run there.
    for key in sorted(inputDict, key=inputDict.get):
        if key.startswith("feederName"):
            feederDir, feederName = inputDict[key].split("___")
            feederList.append(feederName)
            try:
                os.remove(pJoin(modelDir, feederName, "allOutputData.json"))
                fs.remove(pJoin(modelDir, feederName, "allOutputData.json"))
            except Exception, e:
                pass
            if not os.path.isdir(pJoin(modelDir, feederName)):
                # create subfolders for feeders
                os.makedirs(pJoin(modelDir, feederName))

            fs.export_from_fs_to_local(pJoin("data", "Feeder", feederDir, feederName + ".json"),
                                             pJoin(modelDir, feederName, "feeder.json"))
            inputDict["climateName"], latforpvwatts = zipCodeToClimateName(
                inputDict["zipCode"], fs)
            fs.export_from_fs_to_local(pJoin("data", "Climate", inputDict["climateName"] + ".tmy2"),
                                       pJoin(modelDir, feederName, "climate.tmy2"))
            try:
                startTime = datetime.datetime.now()
                feederJson = json.load(
                    open(pJoin(modelDir, feederName, "feeder.json")))
                tree = feederJson["tree"]
                # Set up GLM with correct time and recorders:
                feeder.attachRecorders(
                    tree, "Regulator", "object", "regulator")
                feeder.attachRecorders(
                    tree, "Capacitor", "object", "capacitor")
                feeder.attachRecorders(tree, "Inverter", "object", "inverter")
                feeder.attachRecorders(
                    tree, "Windmill", "object", "windturb_dg")
                feeder.attachRecorders(tree, "CollectorVoltage", None, None)
                feeder.attachRecorders(tree, "Climate", "object", "climate")
                feeder.attachRecorders(tree, "OverheadLosses", None, None)
                feeder.attachRecorders(tree, "UndergroundLosses", None, None)
                feeder.attachRecorders(tree, "TriplexLosses", None, None)
                feeder.attachRecorders(tree, "TransformerLosses", None, None)
                feeder.groupSwingKids(tree)
                feeder.adjustTime(tree=tree, simLength=float(inputDict["simLength"]),
                                  simLengthUnits=inputDict["simLengthUnits"], simStartDate=inputDict["simStartDate"])
                # RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
                rawOut = gridlabd.runInFilesystem(tree, attachments=feederJson["attachments"],
                                                  keepFiles=True, workDir=pJoin(modelDir, feederName))
                cleanOut = {}
                # Std Err and Std Out
                cleanOut['stderr'] = rawOut['stderr']
                cleanOut['stdout'] = rawOut['stdout']
                # Time Stamps
                for key in rawOut:
                    if '# timestamp' in rawOut[key]:
                        cleanOut['timeStamps'] = rawOut[key]['# timestamp']
                        break
                    elif '# property.. timestamp' in rawOut[key]:
                        cleanOut['timeStamps'] = rawOut[
                            key]['# property.. timestamp']
                    else:
                        cleanOut['timeStamps'] = []
                # Day/Month Aggregation Setup:
                stamps = cleanOut.get('timeStamps', [])
                level = inputDict.get('simLengthUnits', 'hours')
                # Climate
                for key in rawOut:
                    if key.startswith('Climate_') and key.endswith('.csv'):
                        cleanOut['climate'] = {}
                        cleanOut['climate'][
                            'Rain Fall (in/h)'] = hdmAgg(rawOut[key].get('rainfall'), sum, level, stamps)
                        cleanOut['climate'][
                            'Wind Speed (m/s)'] = hdmAgg(rawOut[key].get('wind_speed'), avg, level, stamps)
                        cleanOut['climate']['Temperature (F)'] = hdmAgg(
                            rawOut[key].get('temperature'), max, level, stamps)
                        cleanOut['climate']['Snow Depth (in)'] = hdmAgg(
                            rawOut[key].get('snowdepth'), max, level, stamps)
                        cleanOut['climate'][
                            'Direct Insolation (W/m^2)'] = hdmAgg(rawOut[key].get('solar_direct'), sum, level, stamps)
                # Voltage Band
                if 'VoltageJiggle.csv' in rawOut:
                    cleanOut['allMeterVoltages'] = {}
                    cleanOut['allMeterVoltages']['Min'] = hdmAgg(
                        [float(i / 2) for i in rawOut['VoltageJiggle.csv']['min(voltage_12.mag)']], min, level, stamps)
                    cleanOut['allMeterVoltages']['Mean'] = hdmAgg(
                        [float(i / 2) for i in rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)']], avg, level, stamps)
                    cleanOut['allMeterVoltages']['StdDev'] = hdmAgg(
                        [float(i / 2) for i in rawOut['VoltageJiggle.csv']['std(voltage_12.mag)']], avg, level, stamps)
                    cleanOut['allMeterVoltages']['Max'] = hdmAgg(
                        [float(i / 2) for i in rawOut['VoltageJiggle.csv']['max(voltage_12.mag)']], max, level, stamps)
                # Power Consumption
                cleanOut['Consumption'] = {}
                # Set default value to be 0, avoiding missing value when
                # computing Loads
                cleanOut['Consumption']['Power'] = [
                    0] * int(inputDict["simLength"])
                cleanOut['Consumption']['Losses'] = [
                    0] * int(inputDict["simLength"])
                cleanOut['Consumption']['DG'] = [
                    0] * int(inputDict["simLength"])
                for key in rawOut:
                    if key.startswith('SwingKids_') and key.endswith('.csv'):
                        oneSwingPower = hdmAgg(vecPyth(
                            rawOut[key]['sum(power_in.real)'], rawOut[key]['sum(power_in.imag)']), avg, level, stamps)
                        if 'Power' not in cleanOut['Consumption']:
                            cleanOut['Consumption']['Power'] = oneSwingPower
                        else:
                            cleanOut['Consumption']['Power'] = vecSum(
                                oneSwingPower, cleanOut['Consumption']['Power'])
                    elif key.startswith('Inverter_') and key.endswith('.csv'):
                        realA = rawOut[key]['power_A.real']
                        realB = rawOut[key]['power_B.real']
                        realC = rawOut[key]['power_C.real']
                        imagA = rawOut[key]['power_A.imag']
                        imagB = rawOut[key]['power_B.imag']
                        imagC = rawOut[key]['power_C.imag']
                        oneDgPower = hdmAgg(vecSum(vecPyth(realA, imagA), vecPyth(
                            realB, imagB), vecPyth(realC, imagC)), avg, level, stamps)
                        if 'DG' not in cleanOut['Consumption']:
                            cleanOut['Consumption']['DG'] = oneDgPower
                        else:
                            cleanOut['Consumption']['DG'] = vecSum(
                                oneDgPower, cleanOut['Consumption']['DG'])
                    elif key.startswith('Windmill_') and key.endswith('.csv'):
                        vrA = rawOut[key]['voltage_A.real']
                        vrB = rawOut[key]['voltage_B.real']
                        vrC = rawOut[key]['voltage_C.real']
                        viA = rawOut[key]['voltage_A.imag']
                        viB = rawOut[key]['voltage_B.imag']
                        viC = rawOut[key]['voltage_C.imag']
                        crB = rawOut[key]['current_B.real']
                        crA = rawOut[key]['current_A.real']
                        crC = rawOut[key]['current_C.real']
                        ciA = rawOut[key]['current_A.imag']
                        ciB = rawOut[key]['current_B.imag']
                        ciC = rawOut[key]['current_C.imag']
                        powerA = vecProd(vecPyth(vrA, viA), vecPyth(crA, ciA))
                        powerB = vecProd(vecPyth(vrB, viB), vecPyth(crB, ciB))
                        powerC = vecProd(vecPyth(vrC, viC), vecPyth(crC, ciC))
                        # HACK: multiply by negative one because turbine power
                        # sign is opposite all other DG:
                        oneDgPower = [-1.0 *
                                      x for x in hdmAgg(vecSum(powerA, powerB, powerC), avg, level, stamps)]
                        if 'DG' not in cleanOut['Consumption']:
                            cleanOut['Consumption']['DG'] = oneDgPower
                        else:
                            cleanOut['Consumption']['DG'] = vecSum(
                                oneDgPower, cleanOut['Consumption']['DG'])
                    elif key in ['OverheadLosses.csv', 'UndergroundLosses.csv', 'TriplexLosses.csv', 'TransformerLosses.csv']:
                        realA = rawOut[key]['sum(power_losses_A.real)']
                        imagA = rawOut[key]['sum(power_losses_A.imag)']
                        realB = rawOut[key]['sum(power_losses_B.real)']
                        imagB = rawOut[key]['sum(power_losses_B.imag)']
                        realC = rawOut[key]['sum(power_losses_C.real)']
                        imagC = rawOut[key]['sum(power_losses_C.imag)']
                        oneLoss = hdmAgg(vecSum(vecPyth(realA, imagA), vecPyth(
                            realB, imagB), vecPyth(realC, imagC)), avg, level, stamps)
                        if 'Losses' not in cleanOut['Consumption']:
                            cleanOut['Consumption']['Losses'] = oneLoss
                        else:
                            cleanOut['Consumption']['Losses'] = vecSum(
                                oneLoss, cleanOut['Consumption']['Losses'])
                # Aggregate up the timestamps:
                if level == 'days':
                    cleanOut['timeStamps'] = aggSeries(
                        stamps, stamps, lambda x: x[0][0:10], 'days')
                elif level == 'months':
                    cleanOut['timeStamps'] = aggSeries(
                        stamps, stamps, lambda x: x[0][0:7], 'months')
                # Write the output.
                with open(pJoin(modelDir, feederName, "allOutputData.json"), "w") as outFile:
                    json.dump(cleanOut, outFile, indent=4)
                # Update the runTime in the input file.
                endTime = datetime.datetime.now()
                inputDict["runTime"] = str(
                    datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
                with open(pJoin(modelDir, feederName, "allInputData.json"), "w") as inFile:
                    json.dump(inputDict, inFile, indent=4)
                # Clean up the PID file.
                os.remove(pJoin(modelDir, feederName, "PID.txt"))
                print "DONE RUNNING GRIDLABMULTI", modelDir, feederName
            except Exception as e:
                print "MODEL CRASHED GRIDLABMULTI", e, modelDir, feederName
                cancel(pJoin(modelDir, feederName))
                with open(pJoin(modelDir, feederName, "stderr.txt"), "a+") as stderrFile:
                    traceback.print_exc(file=stderrFile)
    finishTime = datetime.datetime.now()
    inputDict["runTime"] = str(
        datetime.timedelta(seconds=int((finishTime - beginTime).total_seconds())))
    with open(pJoin(modelDir, "allInputData.json"), "w") as inFile:
        json.dump(inputDict, inFile, indent=4)
    # Integrate data into allOutputData.json, if error happens, cancel it
    try:
        output = {}
        output["failures"] = {}
        numOfFeeders = 0

        files = []
        for froot, _, fname in os.walk(modelDir):
            files.extend(
                [os.path.relpath(os.path.join(froot, f), modelDir) for f in fname])
        logger.info('GridlabD outputs in %s:\n%s', modelDir, pp.pformat(files))

        for root, dirs, files in os.walk(modelDir):
            # dump error info into dict
            if "stderr.txt" in files:
                with open(pJoin(root, "stderr.txt"), "r") as stderrFile:
                    tempString = stderrFile.read()
                    if "ERROR" in tempString or "FATAL" in tempString or "Traceback" in tempString:
                        output["failures"][
                            "feeder_" + str(os.path.split(root)[-1])] = {"stderr": tempString}
                        continue
            # dump simulated data into dict
            if "allOutputData.json" in files:
                with open(pJoin(root, "allOutputData.json"), "r") as feederOutputData:
                    numOfFeeders += 1
                    feederOutput = json.load(feederOutputData)
                    print "Feeder output:  " + json.dumps(feederOutput)
                    # TODO: a better feeder name
                    output["feeder_" + str(os.path.split(root)[-1])] = {}
                    output[
                        "feeder_" + str(os.path.split(root)[-1])]["Consumption"] = feederOutput["Consumption"]
                    output[
                        "feeder_" + str(os.path.split(root)[-1])]["allMeterVoltages"] = feederOutput["allMeterVoltages"]
                    output[
                        "feeder_" + str(os.path.split(root)[-1])]["stderr"] = feederOutput["stderr"]
                    output[
                        "feeder_" + str(os.path.split(root)[-1])]["stdout"] = feederOutput["stdout"]
                    # output[root] = {feederOutput["Consumption"], feederOutput["allMeterVoltages"], feederOutput["stdout"], feederOutput["stderr"]}
        output["numOfFeeders"] = numOfFeeders
        output["timeStamps"] = feederOutput.get("timeStamps", [])
        output["climate"] = feederOutput.get("climate", [])
        fs.save(pJoin(modelDir, "allOutputData.json"), json.dumps(output, indent=4))
        try:
            os.remove(pJoin(modelDir, "PPID.txt"))
        except:
            pass
        # Send email to user on successfully run status of model
        emailStatus = inputDict.get('emailStatus', 0)
        if (emailStatus == "on"):
            print "\n    EMAIL ALERT ON"
            email = session['user_id']
            try:
                user = json.load(fs.open("data/User/" + email + ".json"))
                modelPath, modelName = pSplit(modelDir)
                message = "The model " + "<i>" + str(modelName) + "</i>" + " has successfully completed running. It ran for a total of " + str(
                    inputDict["runTime"]) + " seconds from " + str(beginTime) + ", to " + str(finishTime) + "."
                from omf.web import send_link
                return send_link(email, message, user)
            except Exception, e:
                logger.exception(
                    'ERROR: failed to send model completed running email to user %s. Exception', email)
                # print "ERROR: failed to send model completed running email to
                # user", email, "with exception", e
        else:
            print "\n   EMAIL ALERT NOT ON"

    except Exception, e:
        logger.exception("Gridlab-D model crashed")
        print "MODEL CRASHED GRIDLABMULTI", e, modelDir
        try:
            os.remove(pJoin(modelDir, "PPID.txt"))
        except:
            pass
        # Send email to user on failed running status of model
        email = session['user_id']
        try:
            user = json.load(fs.open("data/User/" + email + ".json"))
            modelPath, modelName = pSplit(modelDir)
            message = "The model " + "<i>" + str(modelName) + "</i>" + " has failed to complete running. It ran for a total of " + str(
                inputDict["runTime"]) + " seconds from " + str(beginTime) + ", to " + str(finishTime) + "."
            return omf.web.send_link(email, message, user)
        except Exception, e:
            logger.exception(
                'ERROR: failed to send model completed running email to user %s. Exception', email)
            print "ERROR: failed to send model failed running email to user", email, "with exception", e
        cancel(modelDir)


def avg(inList):
    ''' Average a list. Really wish this was built-in. '''
    return sum(inList) / len(inList)


def hdmAgg(series, func, level, stamps):
    ''' Simple hour/day/month aggregation for Gridlab. '''
    if level in ['days', 'months']:
        return aggSeries(stamps, series, func, level)
    else:
        return series


def aggSeries(timeStamps, timeSeries, func, level):
    ''' Aggregate a list + timeStamps up to the required time level. '''
    # Different substring depending on what level we aggregate to:
    if level == 'months':
        endPos = 7
    elif level == 'days':
        endPos = 10
    combo = zip(timeStamps, timeSeries)
    # Group by level:
    groupedCombo = _groupBy(
        combo, lambda x1, x2: x1[0][0:endPos] == x2[0][0:endPos])
    # Get rid of the timestamps:
    groupedRaw = [[pair[1] for pair in group] for group in groupedCombo]
    return map(func, groupedRaw)


def _pyth(x, y):
    ''' Compute the third side of a triangle--BUT KEEP SIGNS THE SAME FOR DG. '''
    sign = lambda z: (-1 if z < 0 else 1)
    fullSign = sign(sign(x) * x * x + sign(y) * y * y)
    return fullSign * math.sqrt(x * x + y * y)


def vecPyth(vx, vy):
    ''' Pythagorean theorem for pairwise elements from two vectors. '''
    rows = zip(vx, vy)
    return map(lambda x: _pyth(*x), rows)


def vecSum(*args):
    ''' Add n vectors. '''
    return map(sum, zip(*args))


def _prod(inList):
    ''' Product of all values in a list. '''
    return reduce(lambda x, y: x * y, inList, 1)


def vecProd(*args):
    ''' Multiply n vectors. '''
    return map(_prod, zip(*args))


def threePhasePowFac(ra, rb, rc, ia, ib, ic):
    ''' Get power factor for a row of threephase volts and amps. Gridlab-specific. '''
    pfRow = lambda row: math.cos(
        math.atan((row[0] + row[1] + row[2]) / (row[3] + row[4] + row[5])))
    rows = zip(ra, rb, rc, ia, ib, ic)
    return map(pfRow, rows)


def roundSeries(ser):
    ''' Round everything in a vector to 4 sig figs. '''
    return map(lambda x: roundSig(x, 4), ser)


def _groupBy(inL, func):
    ''' Take a list and func, and group items in place comparing with func. Make sure the func is an equivalence relation, or your brain will hurt. '''
    if inL == []:
        return inL
    if len(inL) == 1:
        return [inL]
    newL = [[inL[0]]]
    for item in inL[1:]:
        if func(item, newL[-1][0]):
            newL[-1].append(item)
        else:
            newL.append([item])
    return newL


def _tests():
    # Variables
    from .. import filesystem
    fs = filesystem.Filesystem().fs
    workDir = pJoin(__metaModel__._omfDir, "data", "Model")
    inData = {"simStartDate": "2012-04-01",
              "simLengthUnits": "hours",
              # "feederName": "admin___Simple Market System",
              # "feederName2": "admin___Simple Market System BROKEN", 		# configure error
              # "feederName3": "public___13 Node Embedded DO NOT SAVE",		# feeder error
              # "feederName4": "public___13 Node Ref Feeder Flat",
              # "feederName5": "public___13 Node Ref Feeder Laid Out ZERO CVR",
              # "feederName6": "public___13 Node Ref Feeder Laid Out",
              # "feederName7": "public___ABEC Columbia",
              # "feederName8": "public___ABEC Frank LO Houses",				# feeder error
              # "feederName9": "public___ABEC Frank LO",
              # "feederName10": "public___ACEC Geo",
              # "feederName11": "public___Battery 13 Node Centralized",
              # "feederName12": "public___Battery 13 Node Distributed",
              # "feederName13": "public___DEC Red Base",
              # "feederName14": "public___DEC Red Battery",
              # "feederName15": "public___DEC Red CVR",
              # "feederName16": "public___DEC Red DG",
              # "feederName17": "public___INEC Renoir",
              # "feederName18": "public___Olin Barre CVR Base",
              # "feederName19": "public___Olin Barre Geo",
              # "feederName20": "public___Olin Barre Housed 05Perc Solar",
              # "feederName21": "public___Olin Barre Housed 20Perc Solar",
              # "feederName22": "public___Olin Barre Housed 50Perc Solar",
              # "feederName23": "public___Olin Barre Housed 90Perc Solar",
              # "feederName24": "public___Olin Barre Housed Battery",
              # "feederName25": "public___Olin Barre Housed Wind",
              # "feederName26": "public___Olin Barre Housed",
              # "feederName27": "public___Olin Barre", 						# feeder error
              # "feederName28": "public___PNNL Taxonomy Feeder 1",
              # "feederName29": "public___Simple Market System Comm Solar",
              # "feederName30": "public___Simple Market System Indy Solar",
              "feederName31": "public___Simple Market System",
              # "feederName": "public___Battery 13 Node Distributed",
              "modelType": "gridlabMulti",
              "zipCode": "64735",
              "simLength": "24",
              "runTime": ""}
    modelLoc = pJoin(workDir, "admin", "Automated Multiple GridlabD Testing")
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
    # Cancel the model.
    # time.sleep(2)
    # cancel(modelLoc)
    # Show the output.
    renderAndShow(template, fs, modelDir=modelLoc)

    # Delete the model.
    # shutil.rmtree(modelLoc)

if __name__ == '__main__':
    _tests()
