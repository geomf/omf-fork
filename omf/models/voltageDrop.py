# Portions Copyrights (C) 2015 Intel Corporation
''' Graph the voltage drop on a feeder. '''

import json
import os
import sys
import tempfile
import webbrowser
import time
import shutil
import subprocess
import datetime as dt
import csv
import math
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import networkx as nx
import __metaModel__
from __metaModel__ import *
import logging

logger = logging.getLogger(__name__)

# OMF imports
sys.path.append(__metaModel__._omfDir)
import omf.feeder
from omf.solvers import gridlabd
from omf.common.plot import Plot

template = None

def renderTemplate(template, fs, modelDir="", absolutePaths=False, datastoreNames={}):
    # Our HTML template for the interface:
    with fs.open("models/voltageDrop.html") as tempFile:
        template = Template(tempFile.read())
    return __metaModel__.renderTemplate(template, fs, modelDir, absolutePaths, datastoreNames)


def run(modelDir, inputDict, fs):
    ''' Run the model in its directory. '''
    logger.info("Running voltageDrop model... modelDir: %s; inputDict: %s", modelDir, inputDict)
    startTime = dt.datetime.now()
    allOutput = {}
    # Check whether model exist or not
    if not fs.exists(modelDir):
        fs.create_dir(modelDir)
        inputDict["created"] = str(dt.datetime.now())
    fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))
    # Copy feeder data into the model directory.
    feederDir, feederName = inputDict["feederName"].split("___")
    fs.copy_within_fs(pJoin("data", "Feeder", feederDir, feederName + ".json"),
                              pJoin(modelDir, "feeder.json"))
    # Create voltage drop plot.
    tree = json.load(fs.open(pJoin(modelDir, "feeder.json"))).get("tree", {})
    if inputDict.get("layoutAlgorithm", "geospatial") == "geospatial":
        neato = False
    else:
        neato = True
    chart = voltPlot(tree, fs, workDir=modelDir, neatoLayout=neato)
    Plot.save_fig(plt, pJoin(modelDir, "output.png"))
    with open(pJoin(modelDir, "output.png"), "rb") as inFile:
        allOutput["voltageDrop"] = inFile.read().encode("base64")
    fs.save(pJoin(modelDir, "allOutputData.json"), json.dumps(allOutput, indent=4))
    # Update the runTime in the input file.
    endTime = dt.datetime.now()
    inputDict["runTime"] = str(
        dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
    fs.save(pJoin(modelDir, "allInputData.json"), json.dumps(inputDict, indent=4))


def voltPlot(tree, fs, workDir=None, neatoLayout=False):
    ''' Draw a color-coded map of the voltage drop on a feeder.
    Returns a matplotlib object. '''
    # Get rid of schedules and climate:
    for key in tree.keys():
        if tree[key].get("argument", "") == "\"schedules.glm\"" or tree[key].get("tmyfile", "") != "":
            del tree[key]
    # Make sure we have a voltDump:

    def safeInt(x):
        try:
            return int(x)
        except:
            return 0
    biggestKey = max([safeInt(x) for x in tree.keys()])
    tree[str(biggestKey * 10)] = {"object":
                                  "voltdump", "filename": "voltDump.csv"}
    # Run Gridlab.
    if not workDir:
        workDir = tempfile.mkdtemp()
        print "gridlabD runInFilesystem with no specified workDir. Working in", workDir
    gridlabOut = gridlabd.runInFilesystem(
        tree, fs, attachments=[], workDir=workDir)
    with fs.open(pJoin(workDir, 'voltDump.csv')) as dumpFile:
        reader = csv.reader(dumpFile)
        reader.next()  # Burn the header.
        keys = reader.next()
        voltTable = []
        for row in reader:
            rowDict = {}
            for pos, key in enumerate(keys):
                rowDict[key] = row[pos]
            voltTable.append(rowDict)
    # Calculate average node voltage deviation. First, helper functions.

    def pythag(x, y):
        ''' For right triangle with sides a and b, return the hypotenuse. '''
        return math.sqrt(x**2 + y**2)

    def digits(x):
        ''' Returns number of digits before the decimal in the float x. '''
        return math.ceil(math.log10(x + 1))

    def avg(l):
        ''' Average of a list of ints or floats. '''
        return sum(l) / len(l)
    # Detect the feeder nominal voltage:
    for key in tree:
        ob = tree[key]
        if type(ob) == dict and ob.get('bustype', '') == 'SWING':
            feedVoltage = float(ob.get('nominal_voltage', 1))
    # Tot it all up.
    nodeVolts = {}
    for row in voltTable:
        allVolts = []
        for phase in ['A', 'B', 'C']:
            phaseVolt = pythag(float(row['volt' + phase + '_real']),
                               float(row['volt' + phase + '_imag']))
            if phaseVolt != 0.0:
                if digits(phaseVolt) > 3:
                    # Normalize to 120 V standard
                    phaseVolt = phaseVolt * (120 / feedVoltage)
                allVolts.append(phaseVolt)
        nodeVolts[row.get('node_name', '')] = avg(allVolts)
    # Color nodes by VOLTAGE.
    fGraph = omf.feeder.treeToNxGraph(tree)
    voltChart = plt.figure(figsize=(10, 10))
    plt.axes(frameon=0)
    plt.axis('off')
    if neatoLayout:
        # HACK: work on a new graph without attributes because graphViz tries
        # to read attrs.
        cleanG = nx.Graph(fGraph.edges())
        cleanG.add_nodes_from(fGraph)
        positions = nx.graphviz_layout(cleanG, prog='neato')
    else:
        positions = {n: fGraph.node[n].get('pos', (0, 0)) for n in fGraph}
    edgeIm = nx.draw_networkx_edges(fGraph, positions)
    nodeIm = nx.draw_networkx_nodes(fGraph,
                                    pos=positions,
                                    node_color=[
                                        nodeVolts.get(n, 0) for n in fGraph.nodes()],
                                    linewidths=0,
                                    node_size=30,
                                    cmap=plt.cm.jet)
    plt.sci(nodeIm)
    plt.clim(110, 130)
    plt.colorbar()
    return voltChart


def cancel(modelDir, fs):
    ''' Voltage drop runs so fast it's pointless to cancel a run. '''
    pass


def _tests():
    # # First just test the charting.
    # tree = json.load(open("../data/Feeder/public/Olin Barre Geo.json")).get("tree",{})
    # chart = voltPlot(tree)
    # chart.savefig("/Users/dwp0/Desktop/testChart.png")
    # plt.show()
    # Variables
    from .. import filesystem
    fs = filesystem.Filesystem().fs
    # Our HTML template for the interface:
    with fs.open(pJoin(__metaModel__._myDir, "voltageDrop.html"), "r") as tempFile:
        template = Template(tempFile.read())
    workDir = pJoin(__metaModel__._omfDir, "data", "Model")
    inData = {"feederName": "public___Olin Barre Geo",
              "modelType": "voltageDrop",
              "runTime": "",
              "layoutAlgorithm": "geospatial"}
    modelLoc = pJoin(workDir, "admin", "Automated voltageDrop Testing")
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
