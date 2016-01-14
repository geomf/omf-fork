# Portions Copyright (C) 2015 Intel Corporation
import csv
import datetime as dt
import json
import tempfile
from matplotlib import pyplot as plt
from os.path import join as pJoin
import logging
# OMF imports
import omf.feeder
from omf.solvers import gridlabd
from omf.common.plot import Plot

logger = logging.getLogger(__name__)


def omfCalibrate(workDir, feederPath, scadaPath):
    '''calibrates a feeder and saves the calibrated tree at a location'''
    logger.info('Calibrating feeder... work dir: %s; feeder path: %s; scada path: %s', workDir, feederPath, scadaPath)
    with open(feederPath, "r") as jsonIn:
        feederJson = json.load(jsonIn)
        tree = feederJson.get("tree", {})
    scadaSubPower, firstDateTime = _processScadaData(workDir, scadaPath)
    # Force FBS powerflow, because NR fails a lot.
    for key in tree:
        if tree[key].get("module", "").lower() == "powerflow":
            tree[key] = {"module": "powerflow", "solver_method": "FBS"}
    # Attach player.
    classOb = {"class": "player", "variable_names": [
        "value"], "variable_types": ["double"]}
    playerOb = {"object": "player", "property": "value",
                "name": "scadaLoads", "file": "subScada.player", "loop": "0"}
    maxKey = omf.feeder.getMaxKey(tree)
    tree[maxKey + 1] = classOb
    tree[maxKey + 2] = playerOb
    # Make loads reference player.
    loadTemplate = {"object": "triplex_load",
                    "power_pf_12": "0.95",
                    "impedance_pf_12": "0.98",
                    "power_pf_12": "0.90",
                    "impedance_fraction_12": "0.7",
                    "power_fraction_12": "0.3"}
    for key in tree:
        ob = tree[key]
        if ob.get("object", "") == "triplex_node" and ob.get("power_12", "") != "":
            newOb = dict(loadTemplate)
            newOb["name"] = ob.get("name", "")
            newOb["parent"] = ob.get("parent", "")
            newOb["phases"] = ob.get("phases", "")
            newOb["nominal_voltage"] = ob.get("nominal_voltage", "")
            newOb["latitude"] = ob.get("latitude", "0")
            newOb["longitude"] = ob.get("longitude", "0")
            oldPow = ob.get("power_12", "").replace("j", "d")
            pythagPower = gridlabd._strClean(oldPow)
            newOb["base_power_12"] = "scadaLoads.value*" + str(pythagPower)
            tree[key] = newOb
    # Search for the substation regulator and attach a recorder there.
    for key in tree:
        if tree[key].get('bustype', '').lower() == 'swing':
            swingName = tree[key].get('name')
    for key in tree:
        if tree[key].get('object', '') in ['regulator', 'overhead_line', 'underground_line', 'transformer', 'fuse'] and tree[key].get('from', '') == swingName:
            regIndex = key
            SUB_REG_NAME = tree[key]['name']
    recOb = {"object": "recorder",
             "parent": SUB_REG_NAME,
             "property": "power_in.real,power_in.imag",
             "file": "caliSub.csv",
             "interval": "900"}
    tree[maxKey + 3] = recOb
    HOURS = 100
    omf.feeder.adjustTime(tree, HOURS, "hours", firstDateTime.strftime("%Y-%m-%d"))
    # Run Gridlabd.
    output = gridlabd.runInFilesystem(tree, keepFiles=True, workDir=workDir)
    # Calculate scaling constant.
    outRealPow = output["caliSub.csv"]["power_in.real"]
    outImagPower = output["caliSub.csv"]["power_in.imag"]
    outAppPowerKw = [
        (x[0]**2 + x[1]**2)**0.5 / 1000 for x in zip(outRealPow, outImagPower)]
    # HACK: ignore first time step in output and input because GLD sometimes
    # breaks the first step.
    SCAL_CONST = sum(scadaSubPower[1:HOURS]) / sum(outAppPowerKw[1:HOURS])
    # Rewrite the subScada.player file so all the power values are multiplied
    # by the SCAL_CONSTANT.
    newPlayData = []
    with open(pJoin(workDir, "subScada.player"), "r") as playerFile:
        for line in playerFile:
            (key, val) = line.split(',')
            newPlayData.append(
                str(key) + ',' + str(float(val) * SCAL_CONST) + "\n")
    with open(pJoin(workDir, "subScadaCalibrated.player"), "w") as playerFile:
        for row in newPlayData:
            playerFile.write(row)
    # Test by running a glm with subScadaCalibrated.player and caliSub.csv2.
    tree[maxKey + 2]["file"] = "subScadaCalibrated.player"
    tree[maxKey + 3]["file"] = "caliSubCheck.csv"
    secondOutput = gridlabd.runInFilesystem(
        tree, keepFiles=True, workDir=workDir)
    plt.figure()
    plt.plot(outAppPowerKw[1:HOURS], label="initialGuess")
    plt.plot(scadaSubPower[1:HOURS], label="scadaSubPower")
    secondAppKw = [(x[0]**2 + x[1]**2)**0.5 / 1000
                   for x in zip(secondOutput["caliSubCheck.csv"]["power_in.real"], secondOutput["caliSubCheck.csv"]["power_in.imag"])]
    plt.plot(secondAppKw[1:HOURS], label="finalGuess")
    plt.legend(loc=3)
    Plot.save_fig(plt, pJoin(workDir, "caliCheckPlot.png"))
    # Write the final output.
    with open(pJoin(workDir, "calibratedFeeder.json"), "w") as outJson:
        playerString = open(pJoin(workDir, "subScadaCalibrated.player")).read()
        feederJson["attachments"]["subScadaCalibrated.player"] = playerString
        feederJson["tree"] = tree
        json.dump(feederJson, outJson, indent=4)
    return


def _processScadaData(workDir, scadaPath):
    '''generate a SCADA player file from raw SCADA data'''
    with open(scadaPath, "r") as scadaFile:
        scadaReader = csv.DictReader(scadaFile, delimiter='\t')
        allData = [row for row in scadaReader]
    scadaSubPower = [float(row["power"]) for row in allData]
    firstDateTime = dt.datetime.strptime(
        allData[1]["timestamp"], "%m/%d/%Y %H:%M:%S")
    # Write the player.
    maxPower = max(scadaSubPower)
    with open(pJoin(workDir, "subScada.player"), "w") as playFile:
        for row in allData:
            timestamp = dt.datetime.strptime(
                row["timestamp"], "%m/%d/%Y %H:%M:%S")
            power = float(row["power"]) / maxPower
            line = timestamp.strftime(
                "%Y-%m-%d %H:%M:%S") + " PST," + str(power) + "\n"
            playFile.write(line)
    return scadaSubPower, firstDateTime


def _tests():
    print "Beginning to test calibrate.py"
    workDir = tempfile.mkdtemp()
    print "Currently working in: ", workDir
    scadaPath = pJoin("uploads", "FrankScada.tsv")
    feederPath = pJoin("data", "Feeder", "public", "ABEC Frank LO.json")
    assert None == omfCalibrate(
        workDir, feederPath, scadaPath), "feeder calibration failed"

if __name__ == '__main__':
    _tests()
