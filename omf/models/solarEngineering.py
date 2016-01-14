# Portions Copyrights (C) 2015 Intel Corporation
''' Powerflow results for one Gridlab instance. '''

import sys
import shutil
import datetime
import gc
import networkx as nx
import matplotlib
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import multiprocessing
from os.path import join as pJoin
from os.path import split as pSplit
from jinja2 import Template
import traceback
import __metaModel__
from __metaModel__ import *

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
from solvers import gridlabd
from pyhdfs import HdfsFileNotFoundException
from weather import zipCodeToClimateName
import logging

logger = logging.getLogger(__name__)

template = None

def renderTemplate(template, fs, modelDir="", absolutePaths=False, datastoreNames={}):
    ''' Render the model template to an HTML string.
    By default render a blank one for new input.
    If modelDir is valid, render results post-model-run.
    If absolutePaths, the HTML can be opened without a server. '''

    # Our HTML template for the interface:
    with fs.open("models/solarEngineering.html") as tempFile:
        template = Template(tempFile.read())

    try:
        inJson = json.load(fs.open(pJoin(modelDir, "allInputData.json")))
        modelPath, modelName = pSplit(modelDir)
        deepPath, user = pSplit(modelPath)
        inJson["modelName"] = modelName
        inJson["user"] = user
        allInputData = json.dumps(inJson)
    except IOError:
        allInputData = None
    try:
        allOutputData = fs.open(pJoin(modelDir, "allOutputData.json")).read()
    except HdfsFileNotFoundException:
        allOutputData = None
    if absolutePaths:
        # Parent of current folder.
        pathPrefix = __metaModel__._omfDir
    else:
        pathPrefix = ""
    try:
        inputDict = json.load(fs.open(pJoin(modelDir, "allInputData.json")))
    except HdfsFileNotFoundException:
        pass
    return template.render(allInputData=allInputData,
                           allOutputData=allOutputData, modelStatus=getStatus(modelDir, fs), pathPrefix=pathPrefix,
                           datastoreNames=datastoreNames)


def run(modelDir, inputDict, fs):
    ''' Run the model in a separate process. web.py calls this to run the model.
    This function will return fast, but results take a while to hit the file system.'''
    # Check whether model exist or not
    if not fs.exists(modelDir):
        fs.create_dir(modelDir)
        inputDict["created"] = str(datetime.datetime.now())
    # MAYBEFIX: remove this data dump. Check showModel in web.py and
    # renderTemplate()
    fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
    # If we are re-running, remove output and old GLD run:
    try:
        fs.remove(pJoin(modelDir, "allOutputData.json"))
        fs.remove(pJoin(modelDir, "gldContainer"))
    except:
        pass
    # Start background process.
    backProc = multiprocessing.Process(
        target=heavyProcessing, args=(modelDir, inputDict,))
    backProc.start()
    print "SENT TO BACKGROUND", modelDir
    fs.save(pJoin(modelDir, "PPID.txt"), str(backProc.pid))

def runForeground(modelDir, inputDict, fs):
    ''' Run the model in the current process. WARNING: LONG RUN TIME. '''
    # Check whether model exist or not
    logger.info("Running solarEngineering model... modelDir: %s; inputDict: %s", modelDir, inputDict)
    if not fs.exists(modelDir):
        fs.create_dir(modelDir)
        inputDict["created"] = str(datetime.datetime.now())
    # MAYBEFIX: remove this data dump. Check showModel in web.py and
    # renderTemplate()
    fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
    # If we are re-running, remove output and old GLD run:
    try:
        fs.remove(pJoin(modelDir, "allOutputData.json"))
    except:
        pass
    try:
        fs.remove(pJoin(modelDir, "gldContainer"))
    except:
        pass
    # Start process.
    fs.save(pJoin(modelDir, "PPID.txt"), '-999')
    heavyProcessing(modelDir, inputDict, fs)


def heavyProcessing(modelDir, inputDict, fs):
    ''' Run the model in its directory. WARNING: GRIDLAB CAN TAKE HOURS TO COMPLETE. '''
    print "STARTING TO RUN", modelDir
    beginTime = datetime.datetime.now()
    # Get feeder name and data in.
    try:
        fs.create_dir(pJoin(modelDir, 'gldContainer'))
    except:
        pass
    feederDir, feederName = inputDict["feederName"].split("___")
    fs.copy_within_fs(pJoin("data", "Feeder", feederDir, feederName + ".json"),
                pJoin(modelDir, "feeder.json"))
    inputDict["climateName"], latforpvwatts = zipCodeToClimateName(
        inputDict["zipCode"])
    fs.copy_within_fs(pJoin("data", "Climate", inputDict["climateName"] + ".tmy2"),
                pJoin(modelDir, "gldContainer", "climate.tmy2"))
    try:
        startTime = datetime.datetime.now()
        feederJson = json.load(fs.open(pJoin(modelDir, "feeder.json")))
        tree = feederJson["tree"]
        # Set up GLM with correct time and recorders:
        feeder.attachRecorders(tree, "Regulator", "object", "regulator")
        feeder.attachRecorders(tree, "Capacitor", "object", "capacitor")
        feeder.attachRecorders(tree, "Inverter", "object", "inverter")
        feeder.attachRecorders(tree, "Windmill", "object", "windturb_dg")
        feeder.attachRecorders(tree, "CollectorVoltage", None, None)
        feeder.attachRecorders(tree, "Climate", "object", "climate")
        feeder.attachRecorders(tree, "OverheadLosses", None, None)
        feeder.attachRecorders(tree, "UndergroundLosses", None, None)
        feeder.attachRecorders(tree, "TriplexLosses", None, None)
        feeder.attachRecorders(tree, "TransformerLosses", None, None)
        feeder.groupSwingKids(tree)
        # Attach recorders for system voltage map:
        stub = {'object': 'group_recorder', 'group': '"class=node"',
                'property': 'voltage_A', 'interval': 3600, 'file': 'aVoltDump.csv'}
        for phase in ['A', 'B', 'C']:
            copyStub = dict(stub)
            copyStub['property'] = 'voltage_' + phase
            copyStub['file'] = phase.lower() + 'VoltDump.csv'
            tree[feeder.getMaxKey(tree) + 1] = copyStub
        feeder.adjustTime(tree=tree, simLength=float(inputDict["simLength"]),
                          simLengthUnits=inputDict["simLengthUnits"], simStartDate=inputDict["simStartDate"])
        # RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
        rawOut = gridlabd.runInFilesystem(tree, fs, attachments=feederJson["attachments"],
                                          keepFiles=True, workDir=pJoin(modelDir, 'gldContainer'))
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
                cleanOut['timeStamps'] = rawOut[key]['# property.. timestamp']
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
                    'Rain Fall (in/h)'] = hdmAgg(rawOut[key].get('rainfall'), sum, level)
                cleanOut['climate'][
                    'Wind Speed (m/s)'] = hdmAgg(rawOut[key].get('wind_speed'), avg, level)
                cleanOut['climate']['Temperature (F)'] = hdmAgg(
                    rawOut[key].get('temperature'), max, level)
                cleanOut['climate']['Snow Depth (in)'] = hdmAgg(
                    rawOut[key].get('snowdepth'), max, level)
                cleanOut['climate'][
                    'Direct Normal (W/sf)'] = hdmAgg(rawOut[key].get('solar_direct'), sum, level)
                #cleanOut['climate']['Global Horizontal (W/sf)'] = hdmAgg(rawOut[key].get('solar_global'), sum, level)
                climateWbySFList = hdmAgg(
                    rawOut[key].get('solar_global'), sum, level)
                # converting W/sf to W/sm
                climateWbySMList = [x * 10.76392 for x in climateWbySFList]
                cleanOut['climate'][
                    'Global Horizontal (W/sm)'] = climateWbySMList
        # Voltage Band
        if 'VoltageJiggle.csv' in rawOut:
            cleanOut['allMeterVoltages'] = {}
            cleanOut['allMeterVoltages']['Min'] = hdmAgg(
                [float(i / 2) for i in rawOut['VoltageJiggle.csv']['min(voltage_12.mag)']], min, level)
            cleanOut['allMeterVoltages']['Mean'] = hdmAgg(
                [float(i / 2) for i in rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)']], avg, level)
            cleanOut['allMeterVoltages']['StdDev'] = hdmAgg(
                [float(i / 2) for i in rawOut['VoltageJiggle.csv']['std(voltage_12.mag)']], avg, level)
            cleanOut['allMeterVoltages']['Max'] = hdmAgg(
                [float(i / 2) for i in rawOut['VoltageJiggle.csv']['max(voltage_12.mag)']], max, level)
        # Power Consumption
        cleanOut['Consumption'] = {}
        # Set default value to be 0, avoiding missing value when computing
        # Loads
        cleanOut['Consumption']['Power'] = [0] * int(inputDict["simLength"])
        cleanOut['Consumption']['Losses'] = [0] * int(inputDict["simLength"])
        cleanOut['Consumption']['DG'] = [0] * int(inputDict["simLength"])
        for key in rawOut:
            if key.startswith('SwingKids_') and key.endswith('.csv'):
                oneSwingPower = hdmAgg(vecPyth(
                    rawOut[key]['sum(power_in.real)'], rawOut[key]['sum(power_in.imag)']), avg, level)
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
                    realB, imagB), vecPyth(realC, imagC)), avg, level)
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
                oneDgPower = hdmAgg(vecSum(powerA, powerB, powerC), avg, level)
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
                    realB, imagB), vecPyth(realC, imagC)), avg, level)
                if 'Losses' not in cleanOut['Consumption']:
                    cleanOut['Consumption']['Losses'] = oneLoss
                else:
                    cleanOut['Consumption']['Losses'] = vecSum(
                        oneLoss, cleanOut['Consumption']['Losses'])
            elif key.startswith('Regulator_') and key.endswith('.csv'):
                # split function to strip off .csv from filename and user rest
                # of the file name as key. for example- Regulator_VR10.csv ->
                # key would be Regulator_VR10
                regName = ""
                regName = key
                newkey = regName.split(".")[0]
                cleanOut[newkey] = {}
                cleanOut[newkey]['RegTapA'] = [0] * int(inputDict["simLength"])
                cleanOut[newkey]['RegTapB'] = [0] * int(inputDict["simLength"])
                cleanOut[newkey]['RegTapC'] = [0] * int(inputDict["simLength"])
                cleanOut[newkey]['RegTapA'] = rawOut[key]['tap_A']
                cleanOut[newkey]['RegTapB'] = rawOut[key]['tap_B']
                cleanOut[newkey]['RegTapC'] = rawOut[key]['tap_C']
                cleanOut[newkey]['RegPhases'] = rawOut[key]['phases'][0]
            elif key.startswith('Capacitor_') and key.endswith('.csv'):
                capName = ""
                capName = key
                newkey = capName.split(".")[0]
                cleanOut[newkey] = {}
                cleanOut[newkey]['Cap1A'] = [0] * int(inputDict["simLength"])
                cleanOut[newkey]['Cap1B'] = [0] * int(inputDict["simLength"])
                cleanOut[newkey]['Cap1C'] = [0] * int(inputDict["simLength"])
                cleanOut[newkey]['Cap1A'] = rawOut[key]['switchA']
                cleanOut[newkey]['Cap1B'] = rawOut[key]['switchB']
                cleanOut[newkey]['Cap1C'] = rawOut[key]['switchC']
                cleanOut[newkey]['CapPhases'] = rawOut[key]['phases'][0]
        # What percentage of our keys have lat lon data?
        latKeys = [tree[key]['latitude']
                   for key in tree if 'latitude' in tree[key]]
        latPerc = 1.0 * len(latKeys) / len(tree)
        if latPerc < 0.25:
            doNeato = True
        else:
            doNeato = False
        # Generate the frames for the system voltage map time traveling chart.
        genTime = generateVoltChart(
            tree, rawOut, modelDir, neatoLayout=doNeato)
        cleanOut['genTime'] = genTime
        # Aggregate up the timestamps:
        if level == 'days':
            cleanOut['timeStamps'] = aggSeries(
                stamps, stamps, lambda x: x[0][0:10], 'days')
        elif level == 'months':
            cleanOut['timeStamps'] = aggSeries(
                stamps, stamps, lambda x: x[0][0:7], 'months')
        # Write the output.

        fs.save(pJoin(modelDir, "allOutputData.json"), json.dumps(cleanOut, indent=4))
        # Update the runTime in the input file.
        endTime = datetime.datetime.now()
        inputDict["runTime"] = str(
            datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
        fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
        # Clean up the PID file.
        fs.remove(pJoin(modelDir, "gldContainer", "PID.txt"))
        print "DONE RUNNING", modelDir
    except Exception as e:
        print "MODEL CRASHED", e
        # Cancel to get rid of extra background processes.
        try:
            fs.remove(pJoin(modelDir, 'PPID.txt'))
        except:
            pass
        thisErr = traceback.format_exc()
        inputDict['stderr'] = thisErr
        with open(os.path.join(modelDir, 'stderr.txt'), 'w') as errorFile:
            errorFile.write(thisErr)
        # Dump input with error included.
        fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
    finishTime = datetime.datetime.now()
    inputDict["runTime"] = str(
        datetime.timedelta(seconds=int((finishTime - beginTime).total_seconds())))
    fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
    try:
        fs.remove(pJoin(modelDir, "PPID.txt"))
    except:
        pass


def generateVoltChart(tree, rawOut, modelDir, neatoLayout=True):
    ''' Map the voltages on a feeder over time using a movie.'''
    # We need to timestamp frames with the system clock to make sure the
    # browser caches them appropriately.
    genTime = str(datetime.datetime.now()).replace(':', '.')
    # Detect the feeder nominal voltage:
    for key in tree:
        ob = tree[key]
        if type(ob) == dict and ob.get('bustype', '') == 'SWING':
            feedVoltage = float(ob.get('nominal_voltage', 1))
    # Make a graph object.
    fGraph = feeder.treeToNxGraph(tree)
    if neatoLayout:
        # HACK: work on a new graph without attributes because graphViz tries
        # to read attrs.
        cleanG = nx.Graph(fGraph.edges())
        cleanG.add_nodes_from(fGraph)
        positions = nx.graphviz_layout(cleanG, prog='neato')
    else:
        rawPositions = {n: fGraph.node[n].get('pos', (0, 0)) for n in fGraph}
        # HACK: the import code reverses the y coords.

        def yFlip(pair):
            try:
                return (pair[0], -1.0 * pair[1])
            except:
                return (0, 0)
        positions = {k: yFlip(rawPositions[k]) for k in rawPositions}
    # Plot all time steps.
    nodeVolts = {}
    for step, stamp in enumerate(rawOut['aVoltDump.csv']['# timestamp']):
        # Build voltage map.
        nodeVolts[step] = {}
        for nodeName in [x for x in rawOut['aVoltDump.csv'].keys() if x != '# timestamp']:
            allVolts = []
            for phase in ['a', 'b', 'c']:
                voltStep = rawOut[phase + 'VoltDump.csv'][nodeName][step]
                # HACK: Gridlab complex number format sometimes uses i,
                # sometimes j, sometimes d. WTF?
                if type(voltStep) is str:
                    voltStep = voltStep.replace('i', 'j')
                v = complex(voltStep)
                phaseVolt = abs(v)
                if phaseVolt != 0.0:
                    if _digits(phaseVolt) > 3:
                        # Normalize to 120 V standard
                        phaseVolt = phaseVolt * (120 / feedVoltage)
                    allVolts.append(phaseVolt)
            # HACK: Take average of all phases to collapse dimensionality.
            nodeVolts[step][nodeName] = avg(allVolts)
    # Draw animation.
    voltChart = plt.figure(figsize=(10, 10))
    plt.axes(frameon=0)
    plt.axis('off')
    voltChart.subplots_adjust(
        left=0.03, bottom=0.03, right=0.97, top=0.97, wspace=None, hspace=None)
    custom_cm = matplotlib.colors.LinearSegmentedColormap.from_list(
        'custColMap', [(0.0, 'blue'), (0.25, 'darkgray'), (0.75, 'darkgray'), (1.0, 'yellow')])
    edgeIm = nx.draw_networkx_edges(fGraph, positions)
    nodeIm = nx.draw_networkx_nodes(fGraph,
                                    pos=positions,
                                    node_color=[
                                        nodeVolts[0].get(n, 0) for n in fGraph.nodes()],
                                    linewidths=0,
                                    node_size=30,
                                    cmap=custom_cm)
    plt.sci(nodeIm)
    plt.clim(110, 130)
    plt.colorbar()
    plt.title(rawOut['aVoltDump.csv']['# timestamp'][0])

    def update(step):
        nodeColors = np.array([nodeVolts[step].get(n, 0)
                               for n in fGraph.nodes()])
        plt.title(rawOut['aVoltDump.csv']['# timestamp'][step])
        nodeIm.set_array(nodeColors)
        return nodeColors,
    anim = FuncAnimation(voltChart, update, frames=len(
        rawOut['aVoltDump.csv']['# timestamp']), interval=200, blit=False)
    anim.save(pJoin(modelDir, 'voltageChart.mp4'),
              codec='h264', extra_args=['-pix_fmt', 'yuv420p'])
    # Reclaim memory by closing, deleting and garbage collecting the last
    # chart.
    voltChart.clf()
    plt.close()
    del voltChart
    gc.collect()
    return genTime


def avg(inList):
    ''' Average a list. Really wish this was built-in. '''
    return sum(inList) / len(inList)


def hdmAgg(series, func, level):
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


def _digits(x):
    ''' Returns number of digits before the decimal in the float x. '''
    return math.ceil(math.log10(x + 1))


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
    inData = {"simStartDate": "2012-04-01",
              "simLengthUnits": "hours",
              "feederName": "public___Olin Barre GH EOL Solar",
              "modelType": "solarEngineering",
              "zipCode": "64735",
              "simLength": "24",
              "runTime": ""}
    modelLoc = pJoin(__metaModel__._omfDir, "data", "Model",
                     "admin", "Automated solarEngineering Test")
    # Blow away old test results if necessary.
    try:
        shutil.rmtree(modelLoc)
    except:
        # No previous test results.
        pass
    # No-input template.
    # renderAndShow(template)
    # Run the model.
    runForeground(modelLoc, fs, inData)
    # Cancel the model.
    # time.sleep(2)
    # cancel(modelLoc)
    # Show the output.
    renderAndShow(template, fs, modelDir=modelLoc)
    # Delete the model.
    # shutil.rmtree(modelLoc)

if __name__ == '__main__':
    _tests()
